import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.audit.models import AuditEvent
from apps.documents.models import Document
from apps.entities.models import Entity
from apps.meetings.models import AgendaItem, Meeting
from apps.rbac.models import Role
from apps.rbac.services import assign_role
from apps.resolutions.models import Resolution

User = get_user_model()


@pytest.fixture
def world(db):
    cosec = User.objects.create_user(email="cosec-se@cni.test", password="pw-strong-123", name="Cosec")
    assign_role(actor=cosec, user=cosec, role=Role.COMPANY_SECRETARY, entity=None)
    entity = Entity.objects.create(legal_name="Alpha", code="AL", cac_rc_number="123456")
    director = User.objects.create_user(email="dir-se@cni.test", password="pw-strong-123")
    assign_role(actor=cosec, user=director, role=Role.NON_EXECUTIVE_DIRECTOR, entity=entity)
    return cosec, entity, director


@pytest.mark.django_db
def test_search_spans_types_and_respects_scope(world, mfa_client_factory):
    cosec, entity, director = world
    other = Entity.objects.create(legal_name="Beta")
    Meeting.objects.create(entity=entity, title="Budget review board", starts_at=timezone.now())
    Document.objects.create(entity=entity, title="Budget paper")
    Resolution.objects.create(entity=entity, number="AL/BD/2026/001", year=2026, title="Approve budget", text="THAT ...")
    Meeting.objects.create(entity=other, title="Budget secret Beta", starts_at=timezone.now())

    res = mfa_client_factory(director).get("/api/search/?q=budget").json()["results"]
    kinds = {r["kind"] for r in res}
    assert {"meeting", "document", "resolution"} <= kinds
    assert not any("Beta" in r["title"] for r in res)  # scope holds


@pytest.mark.django_db
def test_search_excludes_recused_papers(world, mfa_client_factory):
    cosec, entity, director = world
    meeting = Meeting.objects.create(entity=entity, title="Q3", starts_at=timezone.now())
    item = AgendaItem.objects.create(meeting=meeting, title="Sable award", position=1)
    Document.objects.create(entity=entity, title="Sable contract dossier", meeting=meeting, agenda_item=item)

    client = mfa_client_factory(director)
    assert any(r["title"] == "Sable contract dossier" for r in client.get("/api/search/?q=sable").json()["results"])
    client.post("/api/conflicts/", {"meeting": meeting.pk, "agenda_item": item.pk}, format="json")
    after = client.get("/api/search/?q=sable").json()["results"]
    assert not any(r["kind"] == "document" and r["title"] == "Sable contract dossier" for r in after)


@pytest.mark.django_db
def test_exports_admin_only_and_render_pdf(world, mfa_client_factory):
    cosec, entity, director = world
    Meeting.objects.create(entity=entity, title="Q1", starts_at=timezone.now())
    Resolution.objects.create(entity=entity, number="AL/BD/2026/002", year=2026, title="R", text="T")

    admin = mfa_client_factory(cosec)
    for kind in ("minute-book", "resolution-register", "attendance-register", "audit-extract"):
        r = admin.get(f"/api/exports/{kind}/?entity={entity.pk}")
        assert r.status_code == 200 and r["Content-Type"] == "application/pdf"
        assert bytes(r.content[:5]) == b"%PDF-"
    assert AuditEvent.objects.filter(action="export.generated").count() == 4

    assert mfa_client_factory(director).get(f"/api/exports/minute-book/?entity={entity.pk}").status_code == 403
    assert admin.get(f"/api/exports/nonsense/?entity={entity.pk}").status_code == 404
