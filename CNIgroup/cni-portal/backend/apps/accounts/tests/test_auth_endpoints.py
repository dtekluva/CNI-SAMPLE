import pytest
from django.contrib.auth import get_user_model
from django_otp.plugins.otp_totp.models import TOTPDevice
from rest_framework.test import APIClient

User = get_user_model()


@pytest.mark.django_db
def test_session_login_logout():
    User.objects.create_user(email="dir@cni.test", password="pw-strong-123")
    client = APIClient()

    assert client.get("/api/auth/session/").json()["authenticated"] is False

    ok = client.post("/api/auth/login/", {"email": "dir@cni.test", "password": "pw-strong-123"}, format="json")
    assert ok.status_code == 200

    s = client.get("/api/auth/session/").json()
    assert s["authenticated"] is True and s["mfa_verified"] is False  # password only, MFA pending

    assert client.post("/api/auth/logout/").status_code == 200
    assert client.get("/api/auth/session/").json()["authenticated"] is False


@pytest.mark.django_db
def test_login_rejects_bad_credentials():
    User.objects.create_user(email="dir@cni.test", password="pw-strong-123")
    client = APIClient()
    bad = client.post("/api/auth/login/", {"email": "dir@cni.test", "password": "wrong"}, format="json")
    assert bad.status_code == 401


@pytest.mark.django_db
def test_mfa_enroll_is_idempotent_and_stable():
    """Reloading the enrol page must reuse the same secret, not mint a new device each time."""
    user = User.objects.create_user(email="dir@cni.test", password="pw-strong-123")
    client = APIClient()
    client.force_login(user)

    first = client.post("/api/auth/mfa/enroll/", format="json")
    assert first.status_code == 201
    url1 = first.json()["config_url"]

    second = client.post("/api/auth/mfa/enroll/", format="json")
    assert second.json()["config_url"] == url1  # same secret on reload
    assert TOTPDevice.objects.devices_for_user(user, confirmed=False).count() == 1  # no pile-up


@pytest.mark.django_db
def test_mfa_enroll_reports_already_enrolled_without_leaking_secret():
    user = User.objects.create_user(email="dir@cni.test", password="pw-strong-123")
    TOTPDevice.objects.create(user=user, name="d", confirmed=True)
    client = APIClient()
    client.force_login(user)

    resp = client.post("/api/auth/mfa/enroll/", format="json")
    assert resp.status_code == 200
    body = resp.json()
    assert body == {"enrolled": True}  # no new config_url handed out
    assert client.get("/api/auth/session/").json()["mfa_enrolled"] is True
