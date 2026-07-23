"""
Immutable, tamper-evident audit log (NFR-AUD-1).

Every content access and mutation across the portal records an AuditEvent.
Events are append-only and hash-chained: each event's `hash` covers its own
content plus the previous event's hash, so altering any past row breaks the
chain and `verify_chain()` detects it.

NOTE (production hardening): model-level guards below block updates/deletes via
the ORM. Defence-in-depth for production is to also REVOKE UPDATE/DELETE on this
table at the database role level so bulk/raw paths can't rewrite history either.
"""
import hashlib
import json

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone


class AuditEventManager(models.Manager):
    def record(self, action, actor=None, target=None, metadata=None, ip=None, device=None):
        """The one supported way to write an event."""
        event = self.model(
            actor=actor,
            action=action,
            metadata=metadata or {},
            ip_address=ip,
            device=device or "",
        )
        if target is not None:
            event.content_type = ContentType.objects.get_for_model(target)
            event.object_id = str(target.pk)
        event.save()
        return event


class AuditEvent(models.Model):
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_events",
    )
    action = models.CharField(max_length=128)
    content_type = models.ForeignKey(
        ContentType, null=True, blank=True, on_delete=models.SET_NULL
    )
    object_id = models.CharField(max_length=64, blank=True, default="")
    target = GenericForeignKey("content_type", "object_id")
    metadata = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    device = models.CharField(max_length=256, blank=True, default="")
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    prev_hash = models.CharField(max_length=64, blank=True, default="")
    hash = models.CharField(max_length=64, blank=True, default="")

    objects = AuditEventManager()

    class Meta:
        ordering = ("id",)

    def _payload(self):
        """Canonical, order-stable serialization used for hashing."""
        return json.dumps(
            {
                "prev_hash": self.prev_hash,
                "actor_id": self.actor_id,
                "action": self.action,
                "content_type_id": self.content_type_id,
                "object_id": self.object_id,
                "metadata": self.metadata,
                "ip_address": self.ip_address,
                "device": self.device,
                "timestamp": self.timestamp.isoformat() if self.timestamp else "",
            },
            sort_keys=True,
            default=str,
        )

    def compute_hash(self):
        return hashlib.sha256(self._payload().encode()).hexdigest()

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise ValueError("AuditEvent is append-only; updates are not permitted.")
        if not self.timestamp:
            self.timestamp = timezone.now()
        last = AuditEvent.objects.order_by("-id").first()
        self.prev_hash = last.hash if last else ""
        self.hash = self.compute_hash()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError("AuditEvent is append-only; deletes are not permitted.")

    def __str__(self):
        return f"{self.timestamp:%Y-%m-%d %H:%M} {self.action}"


def verify_chain():
    """Return True iff the whole chain is intact (no tampering)."""
    prev = ""
    for event in AuditEvent.objects.order_by("id"):
        if event.prev_hash != prev:
            return False
        if event.compute_hash() != event.hash:
            return False
        prev = event.hash
    return True
