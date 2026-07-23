import pytest
from django.contrib.auth import get_user_model

from apps.audit.models import AuditEvent
from apps.entities.models import Entity
from apps.rbac.models import Role
from apps.rbac.services import assign_role
from apps.registers.models import RegisterEntry, RegisterType

User = get_user_model()


@pytest.fixture
def cosec(db):
    u = User.objects.create_user(email="cosec@cni.test", password="pw-strong-123")
    assign_role(actor=u, user=u, role=Role.COMPANY_SECRETARY, entity=None)
    return u


@pytest.mark.django_db
def test_cosec_adds_member_entry_and_it_is_audited(cosec, mfa_client_factory):
    entity = Entity.objects.create(legal_name="CNI Holdings")
    client = mfa_client_factory(cosec)
    resp = client.post(
        "/api/registers/",
        {
            "entity": entity.pk,
            "register_type": RegisterType.MEMBERS,
            "party_name": "Ada Bello",
            "particulars": {"shares": 1000, "class": "ordinary"},
            "effective_from": "2020-01-01",
        },
        format="json",
    )
    assert resp.status_code == 201, resp.content
    assert resp.json()["is_active"] is True
    assert AuditEvent.objects.filter(action="register.entry.added").exists()


@pytest.mark.django_db
def test_list_is_entity_scoped_and_filterable(cosec, mfa_client_factory):
    a = Entity.objects.create(legal_name="Alpha")
    b = Entity.objects.create(legal_name="Beta")
    RegisterEntry.objects.create(entity=a, register_type=RegisterType.DIRECTORS, party_name="Dir A", effective_from="2021-01-01")
    RegisterEntry.objects.create(entity=b, register_type=RegisterType.DIRECTORS, party_name="Dir B", effective_from="2021-01-01")

    director = User.objects.create_user(email="dir@cni.test", password="pw-strong-123")
    assign_role(actor=cosec, user=director, role=Role.NON_EXECUTIVE_DIRECTOR, entity=a)
    names = [e["party_name"] for e in mfa_client_factory(director).get("/api/registers/").json()]
    assert names == ["Dir A"]  # no leak of Beta

    filtered = mfa_client_factory(cosec).get("/api/registers/?register_type=directors&entity=%d" % b.pk).json()
    assert [e["party_name"] for e in filtered] == ["Dir B"]


@pytest.mark.django_db
def test_non_cosec_cannot_write(cosec, mfa_client_factory):
    entity = Entity.objects.create(legal_name="Alpha")
    director = User.objects.create_user(email="dir@cni.test", password="pw-strong-123")
    assign_role(actor=cosec, user=director, role=Role.NON_EXECUTIVE_DIRECTOR, entity=entity)
    resp = mfa_client_factory(director).post(
        "/api/registers/",
        {"entity": entity.pk, "register_type": RegisterType.MEMBERS, "party_name": "X", "effective_from": "2020-01-01"},
        format="json",
    )
    assert resp.status_code == 403


@pytest.mark.django_db
def test_entry_cannot_be_deleted_only_ceased(cosec, mfa_client_factory):
    entity = Entity.objects.create(legal_name="Alpha")
    entry = RegisterEntry.objects.create(
        entity=entity, register_type=RegisterType.MEMBERS, party_name="Ada", effective_from="2020-01-01"
    )
    client = mfa_client_factory(cosec)

    assert client.delete(f"/api/registers/{entry.pk}/").status_code == 405

    resp = client.post(f"/api/registers/{entry.pk}/cease/", {"ceased_on": "2024-06-30"}, format="json")
    assert resp.status_code == 200
    entry.refresh_from_db()
    assert entry.ceased_on.isoformat() == "2024-06-30"
    assert entry.is_active is False
    assert AuditEvent.objects.filter(action="register.entry.ceased").exists()


@pytest.mark.django_db
def test_as_at_shows_historical_position(cosec, mfa_client_factory):
    entity = Entity.objects.create(legal_name="Alpha")
    RegisterEntry.objects.create(
        entity=entity, register_type=RegisterType.MEMBERS, party_name="Former", effective_from="2019-01-01", ceased_on="2021-01-01"
    )
    RegisterEntry.objects.create(
        entity=entity, register_type=RegisterType.MEMBERS, party_name="Current", effective_from="2019-01-01"
    )
    client = mfa_client_factory(cosec)
    # As at 2020, both were members; today only Current remains.
    at_2020 = {e["party_name"] for e in client.get("/api/registers/?as_at=2020-06-01").json()}
    assert at_2020 == {"Former", "Current"}
    active_now = {e["party_name"] for e in client.get("/api/registers/?active=true").json()}
    assert active_now == {"Current"}


@pytest.mark.django_db
def test_directors_roster_joins_shareholding(cosec, mfa_client_factory):
    entity = Entity.objects.create(legal_name="Alpha")
    RegisterEntry.objects.create(
        entity=entity, register_type=RegisterType.DIRECTORS, party_name="Ada Bello",
        effective_from="2020-01-01", particulars={"designation": "Chairman"},
    )
    RegisterEntry.objects.create(
        entity=entity, register_type=RegisterType.MEMBERS, party_name="Ada Bello",
        effective_from="2020-01-01", particulars={"shares": 5000, "class": "ordinary"},
    )
    RegisterEntry.objects.create(  # ceased director, no shareholding
        entity=entity, register_type=RegisterType.DIRECTORS, party_name="Gone Person",
        effective_from="2018-01-01", ceased_on="2022-01-01",
    )
    roster = mfa_client_factory(cosec).get("/api/registers/directors/").json()
    ada = next(r for r in roster if r["name"] == "Ada Bello")
    assert ada["designation"] == "Chairman" and ada["shares"] == 5000 and ada["active"] is True
    gone = next(r for r in roster if r["name"] == "Gone Person")
    assert gone["active"] is False and gone["shares"] is None


@pytest.mark.django_db
def test_director_profile_masks_bvn_for_non_admin_and_audits(cosec, mfa_client_factory):
    entity = Entity.objects.create(legal_name="Alpha")
    entry = RegisterEntry.objects.create(
        entity=entity, register_type=RegisterType.DIRECTORS, party_name="Ada Bello",
        effective_from="2020-01-01",
        particulars={"designation": "Chairman", "bvn": "22110000101",
                     "document_type": "International Passport", "document_number": "A08123456"},
    )
    director = User.objects.create_user(email="dir@cni.test", password="pw-strong-123")
    assign_role(actor=cosec, user=director, role=Role.NON_EXECUTIVE_DIRECTOR, entity=entity)

    # group admin sees the full BVN
    full = mfa_client_factory(cosec).get(f"/api/registers/{entry.pk}/director/").json()
    assert full["bvn"] == "22110000101" and full["document_number"] == "A08123456"

    # entity director sees a masked BVN (last 4 only)
    masked = mfa_client_factory(director).get(f"/api/registers/{entry.pk}/director/").json()
    assert masked["bvn"] == "•••••••0101"

    assert AuditEvent.objects.filter(action="register.director.viewed").count() == 2

    # non-directors register entries 404
    member = RegisterEntry.objects.create(
        entity=entity, register_type=RegisterType.MEMBERS, party_name="X", effective_from="2020-01-01"
    )
    assert mfa_client_factory(cosec).get(f"/api/registers/{member.pk}/director/").status_code == 404
