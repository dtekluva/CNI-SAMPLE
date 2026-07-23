"""
In-meeting mode (FR-MTG-7) and group aggregation (FR-ENT-2).
"""
from django.utils import timezone

from .models import MeetingSession


def get_or_create_session(meeting):
    session, _ = MeetingSession.objects.get_or_create(meeting=meeting)
    return session


def start_session(meeting):
    session = get_or_create_session(meeting)
    session.active = True
    session.started_at = session.started_at or timezone.now()
    session.ended_at = None
    first = meeting.agenda_items.order_by("position", "id").first()
    if first and session.current_item_id is None:
        session.current_item = first
        session.item_started_at = timezone.now()
    session.save()
    return session


def present_item(meeting, item):
    """Presenter moves the floor to an item — 'follow' attendees track this."""
    session = get_or_create_session(meeting)
    session.active = True
    session.current_item = item
    session.item_started_at = timezone.now()
    session.save(update_fields=["active", "current_item", "item_started_at"])
    return session


def end_session(meeting):
    session = get_or_create_session(meeting)
    session.active = False
    session.ended_at = timezone.now()
    session.save(update_fields=["active", "ended_at"])
    return session


def session_state(meeting):
    session = getattr(meeting, "session", None)
    item = session.current_item if session else None
    elapsed = None
    if session and session.item_started_at:
        elapsed = int((timezone.now() - session.item_started_at).total_seconds() // 60)
    return {
        "active": bool(session and session.active),
        "current_item": item.id if item else None,
        "current_item_title": item.title if item else None,
        "current_position": item.position if item else None,
        "allocated_minutes": item.time_allocation_minutes if item else None,
        "elapsed_minutes": elapsed,
        "over": bool(item and item.time_allocation_minutes and elapsed is not None and elapsed > item.time_allocation_minutes),
    }


def group_summary(user):
    """Per-entity rollup across everything the user can see (FR-ENT-2)."""
    from apps.actions.models import Action
    from apps.compliance.models import ComplianceObligation
    from apps.rbac.resolution import entities_for_user
    from apps.resolutions.models import Resolution

    from .models import Meeting

    now = timezone.now()
    today = now.date()
    rows = []
    totals = {"meetings": 0, "upcoming": 0, "open_actions": 0, "overdue_actions": 0, "pending_resolutions": 0, "compliance_red": 0}
    for e in entities_for_user(user).order_by("legal_name"):
        meetings = Meeting.objects.filter(entity=e)
        actions = Action.objects.filter(entity=e, status=Action.Status.OPEN)
        row = {
            "entity": e.id,
            "entity_name": e.legal_name,
            "meetings": meetings.count(),
            "upcoming": meetings.filter(starts_at__gt=now).count(),
            "open_actions": actions.count(),
            "overdue_actions": actions.filter(due_date__lt=today).count(),
            "pending_resolutions": Resolution.objects.filter(entity=e, outcome=Resolution.Outcome.PENDING).count(),
            "compliance_red": sum(1 for o in ComplianceObligation.objects.filter(entity=e) if o.rag == "red"),
        }
        for k in totals:
            totals[k] += row[k]
        rows.append(row)
    return {"entities": rows, "totals": totals}
