import time

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.accounts.services import enroll_totp, record_mfa_verified
from apps.audit.models import AuditEvent

User = get_user_model()
OTP_SESSION_KEY = "otp_device_id"


def _verify_session(client, device):
    """Mark the client's session as OTP-verified (as django_otp.login would)."""
    session = client.session
    session[OTP_SESSION_KEY] = device.persistent_id
    session.save()


@pytest.mark.django_db
def test_login_requires_totp():
    user = User.objects.create_user(email="dir@cni.test", password="pw-strong-123")
    device = enroll_totp(user)  # confirmed device
    client = APIClient()
    client.force_login(user)

    # Authenticated but not OTP-verified -> denied.
    assert client.get("/api/me/").status_code == 403

    # After MFA verification -> allowed.
    _verify_session(client, device)
    resp = client.get("/api/me/")
    assert resp.status_code == 200
    assert resp.json()["email"] == "dir@cni.test"


@pytest.mark.django_db
def test_session_times_out():
    user = User.objects.create_user(email="to@cni.test", password="pw-strong-123")
    device = enroll_totp(user)
    client = APIClient()
    client.force_login(user)
    _verify_session(client, device)

    # Backdate last activity beyond the timeout window.
    session = client.session
    session["last_activity"] = int(time.time()) - 100_000
    session.save()

    assert client.get("/api/me/").status_code in (401, 403)


@pytest.mark.django_db
def test_mfa_events_audited():
    user = User.objects.create_user(email="ev@cni.test", password="pw-strong-123")
    enroll_totp(user)
    record_mfa_verified(user)
    assert AuditEvent.objects.filter(action="mfa.enrolled", actor=user).exists()
    assert AuditEvent.objects.filter(action="mfa.verified", actor=user).exists()


@pytest.mark.django_db
def test_mfa_accept_any_code_bypass(settings, mfa_client_factory):
    """DEMO flag: any non-empty code verifies (real TOTP still required when off)."""
    from django.contrib.auth import get_user_model
    from django_otp.plugins.otp_totp.models import TOTPDevice
    from rest_framework.test import APIClient

    User = get_user_model()
    u = User.objects.create_user(email="bypass@cni.test", password="pw-strong-123")
    TOTPDevice.objects.create(user=u, name="d", confirmed=True)
    client = APIClient()
    client.force_login(u)

    settings.MFA_ACCEPT_ANY_CODE = False
    assert client.post("/api/auth/mfa/verify/", {"token": "000000"}, format="json").status_code == 400

    settings.MFA_ACCEPT_ANY_CODE = True
    assert client.post("/api/auth/mfa/verify/", {"token": "000000"}, format="json").status_code == 200
    # still rejects an empty code
    assert client.post("/api/auth/mfa/verify/", {"token": ""}, format="json").status_code == 400
