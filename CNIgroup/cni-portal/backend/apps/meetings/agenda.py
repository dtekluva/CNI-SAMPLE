from django.db.models import Max

from .models import AgendaItem


def add_item(*, meeting, title, item_type, owner=None, time_allocation_minutes=0):
    next_pos = (meeting.agenda_items.aggregate(m=Max("position"))["m"] or -1) + 1
    return AgendaItem.objects.create(
        meeting=meeting,
        title=title,
        item_type=item_type,
        owner=owner,
        time_allocation_minutes=time_allocation_minutes,
        position=next_pos,
    )


def reorder_items(*, meeting, ordered_ids):
    """Set positions to match the given order (drag-reorder)."""
    for idx, item_id in enumerate(ordered_ids):
        AgendaItem.objects.filter(pk=item_id, meeting=meeting).update(position=idx)


MATTERS_ARISING_TITLE = "Matters arising"


def open_prior_actions(meeting):
    """Open actions of this entity from BEFORE this meeting (FR-MIN-4) — the
    unfinished business the next agenda must carry."""
    from django.db.models import Q

    from apps.actions.models import Action

    return (
        Action.objects.filter(entity=meeting.entity, status=Action.Status.OPEN)
        .filter(Q(meeting__isnull=True) | Q(meeting__starts_at__lt=meeting.starts_at))
        .exclude(meeting=meeting)
        .select_related("meeting")
        .order_by("due_date", "id")
    )


def ensure_matters_arising(*, meeting, actor=None):
    """Idempotently add a 'Matters arising' item near the top of the agenda."""
    item = meeting.agenda_items.filter(title=MATTERS_ARISING_TITLE).first()
    if item:
        return item, False
    item = add_item(meeting=meeting, title=MATTERS_ARISING_TITLE,
                    item_type=AgendaItem.ItemType.DISCUSSION, time_allocation_minutes=10)
    # slot it directly after the opening item (or first if the agenda is empty)
    ids = list(meeting.agenda_items.order_by("position").values_list("id", flat=True))
    ids.remove(item.pk)
    ids.insert(1 if ids else 0, item.pk)
    reorder_items(meeting=meeting, ordered_ids=ids)
    return item, True


def table_of_contents(meeting):
    """Auto-numbered ToC reflecting current order (FR-MTG-3)."""
    return [
        {
            "number": i + 1,
            "id": item.id,
            "title": item.title,
            "type": item.item_type,
            "owner": item.owner_id,
            "minutes": item.time_allocation_minutes,
        }
        for i, item in enumerate(meeting.agenda_items.all())
    ]
