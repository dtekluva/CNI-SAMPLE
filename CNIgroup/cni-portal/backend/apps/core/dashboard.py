"""
Role dashboards (FR-RPT-2). A permission-scoped summary for the signed-in user;
the frontend renders the cards relevant to their role.
"""
from django.utils import timezone

from apps.actions.models import Action
from apps.meetings.models import Meeting
from apps.rbac.resolution import entities_for_user
from apps.resolutions.models import Resolution, Signature


def dashboard_for(user):
    now = timezone.now()
    today = now.date()
    entities = entities_for_user(user)

    upcoming = Meeting.objects.filter(entity__in=entities, starts_at__gte=now).count()
    my_open_actions = Action.objects.filter(owner=user, status=Action.Status.OPEN).count()
    overdue_actions = Action.objects.filter(
        entity__in=entities, status=Action.Status.OPEN, due_date__lt=today
    ).count()

    circulating = Resolution.objects.filter(
        entity__in=entities, kind=Resolution.Kind.CIRCULAR, outcome=Resolution.Outcome.PENDING
    )
    signed_ids = Signature.objects.filter(signer=user).values_list("resolution_id", flat=True)
    awaiting_my_signature = circulating.exclude(id__in=signed_ids).count()

    return {
        "upcoming_meetings": upcoming,
        "my_open_actions": my_open_actions,
        "overdue_actions": overdue_actions,
        "awaiting_my_signature": awaiting_my_signature,
    }
