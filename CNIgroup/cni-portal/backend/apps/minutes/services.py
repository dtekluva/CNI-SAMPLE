from apps.meetings.models import Attendance

from .models import InlineDecision, MinuteBlock, Minutes


def seed_minutes(*, meeting, actor=None):
    """Create draft minutes: one block per agenda item, attendees auto-populated."""
    minutes, _ = Minutes.objects.get_or_create(meeting=meeting)

    present = meeting.attendances.filter(status=Attendance.Status.PRESENT)
    minutes.attendees.set([a.member for a in present])

    for item in meeting.agenda_items.all():
        MinuteBlock.objects.get_or_create(minutes=minutes, agenda_item=item)

    return minutes


def add_inline_decision(*, block, kind, text):
    return InlineDecision.objects.create(block=block, kind=kind, text=text)


def compute_minutes_hash(minutes):
    """A deterministic SHA-256 over the substantive content of the minutes.
    Any edit to a block, the attendee list, or the meeting title changes it —
    so a stored hash proves the signed record has not been altered (FR-MIN-3)."""
    import hashlib

    parts = [minutes.meeting.title]
    for b in minutes.blocks.select_related("agenda_item").order_by("agenda_item__position", "id"):
        parts.append(f"{b.agenda_item.position}␟{b.text}")
    parts.append(",".join(str(pk) for pk in minutes.attendees.order_by("pk").values_list("pk", flat=True)))
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()


def seal_signed(*, minutes, actor):
    """Stamp the immutable seal when minutes are signed."""
    from django.utils import timezone

    minutes.content_hash = compute_minutes_hash(minutes)
    minutes.signed_by = actor
    minutes.signed_at = timezone.now()
    minutes.save(update_fields=["content_hash", "signed_by", "signed_at", "updated_at"])
    return minutes


EDITABLE_STATES = (Minutes.State.DRAFT, Minutes.State.CHAIRMAN_REVIEW, Minutes.State.CIRCULATED)


class MinutesLocked(Exception):
    """Raised when editing is attempted after adoption (the record is fixed)."""


def update_block(*, actor, block, text):
    """Write minute text for an agenda item (FR-MIN-1). Blocked once adopted/signed."""
    from apps.audit.models import AuditEvent

    if block.minutes.state not in EDITABLE_STATES:
        raise MinutesLocked("Minutes are adopted/signed and can no longer be edited.")
    block.text = text
    block.save(update_fields=["text"])
    AuditEvent.objects.record(
        action="minutes.block.updated", actor=actor, target=block.minutes,
        metadata={"agenda_item": block.agenda_item_id},
    )
    return block
