from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.audit.models import AuditEvent
from apps.compliance.models import ComplianceObligation
from apps.entities.models import Entity
from apps.rbac.models import Role
from apps.rbac.services import assign_role

User = get_user_model()


@pytest.fixture
def world(db):
    cosec = User.objects.create_user(email="cosec@cni.test", password="pw-strong-123", name="Cosec")
    assign_role(actor=cosec, user=cosec, role=Role.COMPANY_SECRETARY, entity=None)
    entity = Entity.objects.create(legal_name="Alpha")
    director = User.objects.create_user(email="dir@cni.test", password="pw-strong-123")
    assign_role(actor=cosec, user=director, role=Role.NON_EXECUTIVE_DIRECTOR, entity=entity)
    return cosec, entity, director


@pytest.mark.django_db
def test_rag_statuses(world):
    _, entity, _ = world
    today = timezone.now().date()
    red = ComplianceObligation.objects.create(entity=entity, title="Overdue", regulator="CAC",
                                              due_date=today - timedelta(days=3))
    amber = ComplianceObligation.objects.create(entity=entity, title="Soon", regulator="CBN",
                                                due_date=today + timedelta(days=14))
    green = ComplianceObligation.objects.create(entity=entity, title="Later", regulator="FIRS",
                                                due_date=today + timedelta(days=120))
    assert (red.rag, amber.rag, green.rag) == ("red", "amber", "green")


@pytest.mark.django_db
def test_cosec_creates_directors_read_only(world, mfa_client_factory):
    cosec, entity, director = world
    resp = mfa_client_factory(cosec).post(
        "/api/compliance/",
        {"entity": entity.pk, "title": "CAC Annual Return", "regulator": "CAC",
         "frequency": "annual", "due_date": str(timezone.now().date() + timedelta(days=20))},
        format="json",
    )
    assert resp.status_code == 201 and resp.json()["rag"] == "amber"
    assert AuditEvent.objects.filter(action="compliance.obligation_created").exists()

    denied = mfa_client_factory(director).post(
        "/api/compliance/", {"entity": entity.pk, "title": "X", "regulator": "CAC",
                             "due_date": str(timezone.now().date())}, format="json")
    assert denied.status_code == 403
    # but they can see the calendar
    assert len(mfa_client_factory(director).get("/api/compliance/").json()) == 1


@pytest.mark.django_db
def test_filing_records_evidence_and_rolls_due_date(world, mfa_client_factory):
    cosec, entity, _ = world
    today = timezone.now().date()
    ob = ComplianceObligation.objects.create(
        entity=entity, title="CAC Annual Return", regulator="CAC",
        frequency="annual", due_date=today + timedelta(days=10),
    )
    client = mfa_client_factory(cosec)
    resp = client.post(
        f"/api/compliance/{ob.pk}/filings/",
        {"period_label": "FY2025", "filed_on": str(today), "evidence": "CAC ack ref AR-2025-88231"},
        format="json",
    ).json()
    assert resp["filing"]["evidence"] == "CAC ack ref AR-2025-88231"
    ob.refresh_from_db()
    assert ob.due_date == today + timedelta(days=10 + 365)  # rolled forward a year
    assert resp["rag"] == "green"
    assert AuditEvent.objects.filter(action="compliance.filed").exists()

    history = client.get(f"/api/compliance/{ob.pk}/filings/").json()
    assert [f["period_label"] for f in history] == ["FY2025"]


@pytest.mark.django_db
def test_calendar_is_entity_scoped(world, mfa_client_factory):
    cosec, entity, director = world
    other = Entity.objects.create(legal_name="Beta")
    ComplianceObligation.objects.create(entity=entity, title="Mine", regulator="CAC",
                                        due_date=timezone.now().date())
    ComplianceObligation.objects.create(entity=other, title="Beta secret", regulator="CBN",
                                        due_date=timezone.now().date())
    titles = [o["title"] for o in mfa_client_factory(director).get("/api/compliance/").json()]
    assert titles == ["Mine"]
