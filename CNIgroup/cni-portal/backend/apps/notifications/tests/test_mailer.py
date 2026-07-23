import pytest
from django.contrib.auth import get_user_model

import apps.notifications.mailer as mailer
from apps.notifications.mailer import is_configured
from apps.notifications.services import notify

User = get_user_model()


def test_mailer_configured_flag(monkeypatch):
    monkeypatch.delenv("MAILGUN_API_KEY", raising=False)
    monkeypatch.delenv("MAILGUN_DOMAIN", raising=False)
    assert is_configured() is False

    monkeypatch.setenv("MAILGUN_API_KEY", "k")
    monkeypatch.setenv("MAILGUN_DOMAIN", "d")
    assert is_configured() is True


@pytest.mark.django_db
def test_notify_calls_delivery_when_enabled(monkeypatch):
    monkeypatch.setenv("EMAIL_DELIVERY_ENABLED", "true")
    calls = []
    monkeypatch.setattr(mailer, "send_email", lambda **kw: calls.append(kw))

    user = User.objects.create_user(email="dir@cni.test", password="pw-strong-123")
    notify(recipient=user, event_type="pack.published", subject="Pack", link="https://portal/x")

    assert len(calls) == 1  # only the email channel triggers a send
    assert calls[0]["to"] == "dir@cni.test"
    assert "https://portal/x" in calls[0]["text"]  # link-only body (P5)


@pytest.mark.django_db
def test_notify_no_send_when_disabled(monkeypatch):
    monkeypatch.setenv("EMAIL_DELIVERY_ENABLED", "false")
    calls = []
    monkeypatch.setattr(mailer, "send_email", lambda **kw: calls.append(kw))

    user = User.objects.create_user(email="dir@cni.test", password="pw-strong-123")
    notify(recipient=user, event_type="pack.published", subject="Pack", link="l")
    assert calls == []
