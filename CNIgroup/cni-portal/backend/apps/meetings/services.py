from datetime import timedelta

from apps.audit.models import AuditEvent

from .models import Meeting


def generate_series(*, actor, entity, title, meeting_type, first_start, count, interval_days=90):
    """Create a recurring meeting series (e.g. quarterly board meetings)."""
    meetings = []
    for i in range(count):
        meeting = Meeting.objects.create(
            entity=entity,
            title=f"{title} {i + 1}",
            meeting_type=meeting_type,
            starts_at=first_start + timedelta(days=interval_days * i),
        )
        AuditEvent.objects.record(action="meeting.scheduled", actor=actor, target=meeting)
        meetings.append(meeting)
    return meetings
