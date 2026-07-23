import os

from .models import DEFAULT_CHANNELS, Channel, Notification, NotificationPreference


def _email_delivery_enabled():
    return os.getenv("EMAIL_DELIVERY_ENABLED", "false").lower() in ("1", "true", "yes", "on")


def _try_send_email(recipient, subject, body):
    """Best-effort send; the queued Notification record already exists regardless."""
    try:
        from .mailer import send_email

        send_email(to=recipient.email, subject=subject, text=body)
    except Exception:
        pass


def enabled_channels(user, event_type):
    prefs = {
        p.channel: p.enabled
        for p in NotificationPreference.objects.filter(user=user, event_type=event_type)
    }
    channels = []
    for ch in Channel.values:
        default_on = ch in DEFAULT_CHANNELS
        if prefs.get(ch, default_on):
            channels.append(ch)
    return channels


def set_preference(*, user, event_type, channel, enabled):
    pref, _ = NotificationPreference.objects.update_or_create(
        user=user, event_type=event_type, channel=channel, defaults={"enabled": enabled}
    )
    return pref


def notify(*, recipient, event_type, subject, link, content=None):
    """Create notification records on each enabled channel. Email is link-only (P5)."""
    notes = []
    for ch in enabled_channels(recipient, event_type):
        if ch == Channel.EMAIL:
            body = f"{subject}\nOpen in the Portal: {link}"  # link only — never content (P5)
        elif ch == Channel.IN_PORTAL:
            body = content or subject  # in-portal content is behind auth
        else:
            body = f"{subject}: {link}"
        note = Notification.objects.create(
            recipient=recipient, event_type=event_type, channel=ch,
            subject=subject, body=body, link=link,
        )
        if ch == Channel.EMAIL and _email_delivery_enabled():
            _try_send_email(recipient, subject, body)  # body is link-only (P5)
        notes.append(note)
    return notes
