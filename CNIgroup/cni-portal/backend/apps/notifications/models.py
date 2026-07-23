"""
Notifications (FR-NOT-1). Multi-channel with per-event preferences. Critically
(P5): email carries only a link into the Portal, never confidential content.
Actual outbound delivery (real email/SMS) is external and stays human-gated;
this app builds the queue of notification records.
"""
from django.conf import settings
from django.db import models


class Channel(models.TextChoices):
    EMAIL = "email", "Email"
    SMS = "sms", "SMS"
    PUSH = "push", "Push"
    IN_PORTAL = "in_portal", "In-portal"


DEFAULT_CHANNELS = (Channel.EMAIL, Channel.IN_PORTAL)


class NotificationPreference(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notification_prefs")
    event_type = models.CharField(max_length=64)
    channel = models.CharField(max_length=16, choices=Channel.choices)
    enabled = models.BooleanField(default=True)

    class Meta:
        unique_together = ("user", "event_type", "channel")


class Notification(models.Model):
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    event_type = models.CharField(max_length=64)
    channel = models.CharField(max_length=16, choices=Channel.choices)
    subject = models.CharField(max_length=255)
    body = models.TextField()
    link = models.CharField(max_length=512, blank=True, default="")
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
