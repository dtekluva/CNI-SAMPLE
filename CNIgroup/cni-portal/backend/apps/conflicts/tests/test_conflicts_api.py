import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.audit.models import AuditEvent
from apps.conflicts.models import InterestDeclaration
from apps.conflicts.services import conflicted_user_ids
from apps.entities.models import Entity
from apps.meetings.models import AgendaItem, Meeting
from apps.rbac.models import Role
from apps.rbac.services import assign_role

User = get_user_model()


@pytest.fixture
def world(db):
    cosec = User.objects.create_user(email="cosec@cni.test", password="pw-strong-123")
    assign_role(actor=cosec, user=cosec, role=Role.COMPANY_SECRETARY, entity=None)
    entity = Entity.objects.create(legal_name="Alpha")
    director = User.objects.create_user(email="dir@cni.test", password="pw-strong-123", name="Ada Bello")
    assign_role(actor=cosec, user=director, role=Role.NON_EXECUTIVE_DIRECTOR, entity=entity)
    return cosec, entity, director


@pytest.mark.django_db
def test_director_declares_and_withdraws_interest(world, mfa_client_factory):
    _, entity, director = world
    client = mfa_client_factory(director)

    resp = client.post(
        "/api/interests/",
        {"entity": entity.pk, "kind": "directorship", "party": "Sable Capital", "declared_on": "2026-01-10"},
        format="json",
    )
    assert resp.status_code == 201
    interest = InterestDeclaration.objects.get()
    assert interest.director == director  # always the caller, never spoofable
    assert AuditEvent.objects.filter(action="interest.declared").exists()

    assert client.delete(f"/api/interests/{interest.pk}/").status_code == 405
    assert client.post(f"/api/interests/{interest.pk}/withdraw/", {"withdrawn_on": "2026-06-30"}, format="json").status_code == 200
    interest.refresh_from_db()
    assert interest.is_active is False


@pytest.mark.django_db
def test_directors_see_own_interests_cosec_sees_all(world, mfa_client_factory):
    cosec, entity, director = world
    other = User.objects.create_user(email="other@cni.test", password="pw-strong-123")
    assign_role(actor=cosec, user=other, role=Role.NON_EXECUTIVE_DIRECTOR, entity=entity)
    InterestDeclaration.objects.create(entity=entity, director=director, kind="contract", party="X Ltd", declared_on="2026-01-01")
    InterestDeclaration.objects.create(entity=entity, director=other, kind="contract", party="Y Ltd", declared_on="2026-01-01")

    mine = mfa_client_factory(director).get("/api/interests/").json()
    assert [i["party"] for i in mine] == ["X Ltd"]  # no leak of colleagues' interests
    assert len(mfa_client_factory(cosec).get("/api/interests/").json()) == 2


@pytest.mark.django_db
def test_conflict_declaration_feeds_recusal_set(world, mfa_client_factory):
    _, entity, director = world
    meeting = Meeting.objects.create(entity=entity, title="Q3 Board", starts_at=timezone.now())
    item = AgendaItem.objects.create(meeting=meeting, title="Sable contract award", position=1)
    client = mfa_client_factory(director)

    resp = client.post("/api/conflicts/", {"meeting": meeting.pk, "agenda_item": item.pk, "note": "I chair Sable"}, format="json")
    assert resp.status_code == 201
    assert AuditEvent.objects.filter(action="conflict.declared").exists()
    assert director.pk in conflicted_user_ids(meeting, item)
    other_item = AgendaItem.objects.create(meeting=meeting, title="AOB", position=2)
    assert director.pk not in conflicted_user_ids(meeting, other_item)


@pytest.mark.django_db
def test_recusal_hides_conflicted_item_papers(world, mfa_client_factory):
    """FR-RBAC-2 (checkpoint): a declared conflict overrides entity-level access."""
    from apps.documents.models import Document

    cosec, entity, director = world
    meeting = Meeting.objects.create(entity=entity, title="Q3 Board", starts_at=timezone.now())
    contract_item = AgendaItem.objects.create(meeting=meeting, title="Sable contract award", position=1)
    other_item = AgendaItem.objects.create(meeting=meeting, title="Budget", position=2)
    secret = Document.objects.create(entity=entity, title="Sable Contract Paper", meeting=meeting, agenda_item=contract_item)
    normal = Document.objects.create(entity=entity, title="Budget Paper", meeting=meeting, agenda_item=other_item)

    client = mfa_client_factory(director)
    before = {d["title"] for d in client.get("/api/documents/").json()}
    assert {"Sable Contract Paper", "Budget Paper"} <= before  # entity access grants both

    client.post("/api/conflicts/", {"meeting": meeting.pk, "agenda_item": contract_item.pk}, format="json")

    after = {d["title"] for d in client.get("/api/documents/").json()}
    assert "Sable Contract Paper" not in after  # recused: paper gone
    assert "Budget Paper" in after  # unconflicted item unaffected
    assert client.get(f"/api/documents/{secret.pk}/").status_code == 404  # detail blocked too
    assert client.get(f"/api/documents/{secret.pk}/content/").status_code == 404
    assert client.get(f"/api/documents/{secret.pk}/pdf/").status_code == 404

    # cosec (record-keeper) still sees everything
    assert "Sable Contract Paper" in {d["title"] for d in mfa_client_factory(cosec).get("/api/documents/").json()}

    # whole-meeting conflict hides every paper of that meeting
    other_dir = get_user_model().objects.create_user(email="dir2@cni.test", password="pw-strong-123")
    from apps.rbac.services import assign_role as _ar
    from apps.rbac.models import Role as _R
    _ar(actor=cosec, user=other_dir, role=_R.NON_EXECUTIVE_DIRECTOR, entity=entity)
    c2 = mfa_client_factory(other_dir)
    c2.post("/api/conflicts/", {"meeting": meeting.pk}, format="json")
    assert {d["title"] for d in c2.get("/api/documents/").json()} & {"Sable Contract Paper", "Budget Paper"} == set()
