from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.audit.models import AuditEvent
from apps.committees.models import Committee, CommitteeMembership
from apps.entities.models import Entity
from apps.rbac.models import Role
from apps.rbac.services import assign_role

User = get_user_model()


@pytest.fixture
def world(db):
    cosec = User.objects.create_user(email="cosec@cni.test", password="pw-strong-123", name="Cosec")
    assign_role(actor=cosec, user=cosec, role=Role.COMPANY_SECRETARY, entity=None)
    entity = Entity.objects.create(legal_name="Alpha")
    director = User.objects.create_user(email="dir@cni.test", password="pw-strong-123", name="Ada")
    assign_role(actor=cosec, user=director, role=Role.NON_EXECUTIVE_DIRECTOR, entity=entity)
    return cosec, entity, director


@pytest.mark.django_db
def test_cosec_creates_committee_with_charter(world, mfa_client_factory):
    cosec, entity, director = world
    client = mfa_client_factory(cosec)
    resp = client.post(
        "/api/committees/",
        {"entity": entity.pk, "name": "Audit Committee", "charter": "TOR: oversee financial reporting.",
         "charter_adopted_on": "2026-01-15"},
        format="json",
    )
    assert resp.status_code == 201
    assert AuditEvent.objects.filter(action="committee.created").exists()

    # directors can see but not create
    denied = mfa_client_factory(director).post(
        "/api/committees/", {"entity": entity.pk, "name": "Sneaky"}, format="json"
    )
    assert denied.status_code == 403
    assert client.delete(f"/api/committees/{resp.json()['id']}/").status_code == 405


@pytest.mark.django_db
def test_membership_terms_and_rotation(world, mfa_client_factory):
    cosec, entity, director = world
    committee = Committee.objects.create(entity=entity, name="Risk Committee")
    client = mfa_client_factory(cosec)
    today = timezone.now().date()

    appointed = client.post(
        f"/api/committees/{committee.pk}/appoint/",
        {"user": director.pk, "role": "chair", "term_start": str(today - timedelta(days=30)),
         "term_end": str(today + timedelta(days=60))},
        format="json",
    ).json()
    assert appointed["is_active"] is True
    assert appointed["expires_soon"] is True  # inside the 90-day rotation window
    assert AuditEvent.objects.filter(action="committee.member_appointed").exists()

    ended = client.post(
        f"/api/committees/{committee.pk}/end-membership/",
        {"membership": appointed["id"], "ended_on": str(today)},
        format="json",
    )
    assert ended.status_code == 200
    m = CommitteeMembership.objects.get(pk=appointed["id"])
    assert m.is_active is False  # rotated off, record preserved
    assert AuditEvent.objects.filter(action="committee.member_rotated").exists()


@pytest.mark.django_db
def test_report_submit_and_board_notes(world, mfa_client_factory):
    cosec, entity, director = world
    committee = Committee.objects.create(entity=entity, name="Audit Committee")
    dir_client = mfa_client_factory(director)

    submitted = dir_client.post(
        f"/api/committees/{committee.pk}/reports/",
        {"title": "Q2 Audit Committee Report", "summary": "Reviewed the external audit plan; no material findings."},
        format="json",
    ).json()
    assert submitted["status"] == "submitted"
    assert submitted["submitted_by_name"] == "Ada"

    noted = mfa_client_factory(cosec).post(
        f"/api/committees/{committee.pk}/note-report/", {"report": submitted["id"]}, format="json"
    ).json()
    assert noted["status"] == "noted" and noted["noted_at"]
    assert AuditEvent.objects.filter(action="committee.report_noted").exists()


@pytest.mark.django_db
def test_committees_are_entity_scoped(world, mfa_client_factory):
    cosec, entity, director = world
    other = Entity.objects.create(legal_name="Beta")
    Committee.objects.create(entity=entity, name="Audit Committee")
    Committee.objects.create(entity=other, name="Beta Secret Committee")

    names = [c["name"] for c in mfa_client_factory(director).get("/api/committees/").json()]
    assert names == ["Audit Committee"]  # no leak of Beta
