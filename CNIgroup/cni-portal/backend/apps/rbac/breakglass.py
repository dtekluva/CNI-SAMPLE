from datetime import timedelta

from django.utils import timezone

from apps.audit.models import AuditEvent

from .models import BreakGlassGrant


def invoke_break_glass(*, actor, entity, reason, ttl_minutes=30):
    """
    Grant time-boxed emergency content access (FR-RBAC-3). Requires a reason,
    emits a high-severity audit event, and notifies the Company Secretary.
    """
    if not reason or not reason.strip():
        raise ValueError("A reason is required for break-glass access.")

    expires_at = timezone.now() + timedelta(minutes=ttl_minutes)
    grant = BreakGlassGrant.objects.create(
        user=actor, entity=entity, reason=reason, expires_at=expires_at
    )
    AuditEvent.objects.record(
        action="break_glass.invoked",
        actor=actor,
        target=entity,
        metadata={"reason": reason, "expires_at": expires_at.isoformat(), "severity": "high"},
    )
    _notify_company_secretary(actor=actor, entity=entity, reason=reason)
    return grant


def _notify_company_secretary(*, actor, entity, reason):
    """
    Record the cosec-notification intent. Real multi-channel delivery is wired in
    T-G2 (notifications); this guarantees the event is on record now.
    """
    AuditEvent.objects.record(
        action="break_glass.cosec_notified",
        actor=actor,
        target=entity,
        metadata={"reason": reason},
    )
