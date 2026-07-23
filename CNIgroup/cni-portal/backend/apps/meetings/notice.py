"""
Meeting notice & consent to short notice (FR-MTG-2, CAMA).

Minimum notice periods are seeded with CAMA-style defaults and are intended to be
confirmed/overridden per entity by the Company Secretary (D-B5). Dispatching a
notice inside the window requires recorded consent from every recipient. Every
dispatch records proof of service in the audit log.
"""
from django.utils import timezone

from apps.audit.models import AuditEvent

from .models import ConsentToShortNotice

# CAMA-style defaults (days). Cosec-confirmable per entity (D-B5).
NOTICE_DAYS = {"board": 7, "committee": 7, "agm": 21, "egm": 21}


class ShortNoticeError(Exception):
    """Raised when a short-notice meeting is dispatched without full consent."""


def required_notice_days(meeting):
    return NOTICE_DAYS.get(meeting.meeting_type, 7)


def is_short_notice(meeting, as_of=None):
    as_of = as_of or timezone.now()
    return (meeting.starts_at - as_of).days < required_notice_days(meeting)


def record_consent_to_short_notice(*, actor, meeting, member):
    consent, _ = ConsentToShortNotice.objects.get_or_create(meeting=meeting, member=member)
    AuditEvent.objects.record(
        action="notice.short_notice_consent",
        actor=actor,
        target=meeting,
        metadata={"member": member.pk},
    )
    return consent


def dispatch_notice(*, actor, meeting, recipients, as_of=None):
    """Dispatch the notice, recording proof of service; enforce short-notice consent."""
    as_of = as_of or timezone.now()
    if is_short_notice(meeting, as_of):
        consented = set(
            ConsentToShortNotice.objects.filter(meeting=meeting).values_list("member_id", flat=True)
        )
        missing = [r for r in recipients if r.pk not in consented]
        if missing:
            raise ShortNoticeError(
                f"{len(missing)} member(s) have not consented to short notice."
            )
    proofs = []
    for r in recipients:
        proofs.append(
            AuditEvent.objects.record(
                action="notice.dispatched",
                actor=actor,
                target=meeting,
                metadata={"recipient": r.pk, "channel": "email", "dispatched_at": as_of.isoformat()},
            )
        )
    return proofs
