import pytest
from django.contrib.auth import get_user_model

from apps.notifications.services import notify

User = get_user_model()


@pytest.mark.django_db
def test_my_notifications_api(mfa_client_factory):
    me = User.objects.create_user(email="me@cni.test", password="pw-strong-123")
    other = User.objects.create_user(email="other@cni.test", password="pw-strong-123")
    notify(recipient=me, event_type="pack.published", subject="Pack", link="l")
    notify(recipient=other, event_type="pack.published", subject="Pack", link="l")

    client = mfa_client_factory(me)
    items = client.get("/api/notifications/").json()
    assert len(items) == 2  # email + in_portal for me only
    assert all(True for _ in items)

    first = items[0]["id"]
    assert client.post(f"/api/notifications/{first}/read/").json()["read"] is True


@pytest.mark.django_db
def test_preferences_api(mfa_client_factory):
    me = User.objects.create_user(email="me@cni.test", password="pw-strong-123")
    client = mfa_client_factory(me)
    r = client.post(
        "/api/notifications/preferences/",
        {"event_type": "pack.published", "channel": "email", "enabled": False},
        format="json",
    )
    assert r.status_code == 201
    prefs = client.get("/api/notifications/preferences/").json()
    assert {"event_type": "pack.published", "channel": "email", "enabled": False} in prefs
