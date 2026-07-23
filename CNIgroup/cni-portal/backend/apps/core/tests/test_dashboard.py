from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from django_otp.plugins.otp_totp.models import TOTPDevice
from rest_framework.test import APIClient

from apps.actions.services import create_action
from apps.entities.models import Entity
from apps.meetings.models import Meeting
from apps.rbac.models import Role
from apps.rbac.services import assign_role

User = get_user_model()
UTC = ZoneInfo("UTC")


def mfa_client(user):
    device = TOTPDevice.objects.create(user=user, name="d", confirmed=True)
    client = APIClient()
    client.force_login(user)
    session = client.session
    session["otp_device_id"] = device.persistent_id
    session.save()
    return client


@pytest.mark.django_db
def test_dashboard_scoped_to_user():
    a = Entity.objects.create(legal_name="Entity A")
    b = Entity.objects.create(legal_name="Entity B")
    director = User.objects.create_user(email="dir@cni.test", password="pw-strong-123")
    assign_role(actor=director, user=director, role=Role.NON_EXECUTIVE_DIRECTOR, entity=a)

    # One upcoming meeting in A (in scope) and one in B (out of scope).
    Meeting.objects.create(entity=a, title="A Board", starts_at=timezone.now() + timedelta(days=5))
    Meeting.objects.create(entity=b, title="B Board", starts_at=timezone.now() + timedelta(days=5))
    create_action(entity=a, title="My task", owner=director)

    resp = mfa_client(director).get("/api/dashboard/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["upcoming_meetings"] == 1     # only A's meeting (B out of scope)
    assert data["my_open_actions"] == 1


@pytest.mark.django_db
def test_dashboard_requires_mfa():
    user = User.objects.create_user(email="x@cni.test", password="pw-strong-123")
    client = APIClient()
    client.force_login(user)  # authenticated but not MFA-verified
    assert client.get("/api/dashboard/").status_code == 403
