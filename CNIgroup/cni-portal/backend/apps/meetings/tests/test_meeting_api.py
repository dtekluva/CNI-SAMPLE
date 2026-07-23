from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.entities.models import Entity
from apps.meetings.attendance import check_in
from apps.meetings.models import Meeting
from apps.rbac.models import Role
from apps.rbac.services import assign_role

User = get_user_model()


@pytest.mark.django_db
def test_meetings_api_scoped(mfa_client_factory):
    a = Entity.objects.create(legal_name="Entity A")
    b = Entity.objects.create(legal_name="Entity B")
    director = User.objects.create_user(email="dir@cni.test", password="pw-strong-123")
    assign_role(actor=director, user=director, role=Role.NON_EXECUTIVE_DIRECTOR, entity=a)
    Meeting.objects.create(entity=a, title="A Board", starts_at=timezone.now() + timedelta(days=5))
    Meeting.objects.create(entity=b, title="B Board", starts_at=timezone.now() + timedelta(days=5))

    resp = mfa_client_factory(director).get("/api/meetings/")
    titles = [m["title"] for m in resp.json()]
    assert titles == ["A Board"]  # B out of scope


@pytest.mark.django_db
def test_quorum_action(mfa_client_factory):
    entity = Entity.objects.create(legal_name="CNI Pay")
    director = User.objects.create_user(email="dir@cni.test", password="pw-strong-123")
    assign_role(actor=director, user=director, role=Role.NON_EXECUTIVE_DIRECTOR, entity=entity)
    meeting = Meeting.objects.create(entity=entity, title="Board", starts_at=timezone.now() + timedelta(days=5), quorum=1)
    check_in(meeting=meeting, member=director)

    resp = mfa_client_factory(director).get(f"/api/meetings/{meeting.id}/quorum/")
    assert resp.status_code == 200
    assert resp.json()["met"] is True


@pytest.mark.django_db
def test_notice_action(mfa_client_factory):
    entity = Entity.objects.create(legal_name="CNI Pay")
    cosec = User.objects.create_user(email="cosec@cni.test", password="pw-strong-123")
    assign_role(actor=cosec, user=cosec, role=Role.COMPANY_SECRETARY, entity=entity)
    meeting = Meeting.objects.create(entity=entity, title="Board", starts_at=timezone.now() + timedelta(days=30))

    resp = mfa_client_factory(cosec).post(
        f"/api/meetings/{meeting.id}/dispatch_notice/", {"recipients": [cosec.id]}, format="json"
    )
    assert resp.status_code == 200
    assert resp.json()["dispatched"] == 1
