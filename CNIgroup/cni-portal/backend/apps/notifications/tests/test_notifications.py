import pytest
from django.contrib.auth import get_user_model

from apps.notifications.models import Channel
from apps.notifications.services import notify, set_preference

User = get_user_model()


@pytest.mark.django_db
def test_email_contains_link_not_content():
    recipient = User.objects.create_user(email="dir@cni.test", password="pw-strong-123")
    link = "https://portal.cni/meetings/1/pack"
    secret = "CONFIDENTIAL Q3 revenue was 4.2bn"

    notes = notify(
        recipient=recipient, event_type="pack.published",
        subject="Q3 board pack published", link=link, content=secret,
    )
    email = next(n for n in notes if n.channel == Channel.EMAIL)
    assert link in email.body
    assert secret not in email.body  # content never leaves via email (P5)


@pytest.mark.django_db
def test_event_preferences_respected():
    user = User.objects.create_user(email="dir@cni.test", password="pw-strong-123")
    set_preference(user=user, event_type="pack.published", channel=Channel.EMAIL, enabled=False)

    notes = notify(recipient=user, event_type="pack.published", subject="x", link="l")
    channels = {n.channel for n in notes}
    assert Channel.EMAIL not in channels      # disabled by preference
    assert Channel.IN_PORTAL in channels      # default still on
