from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from django.contrib.auth import get_user_model

from apps.entities.models import Entity
from apps.meetings.agenda import add_item
from apps.meetings.attendance import check_in
from apps.meetings.models import AgendaItem, Meeting
from apps.minutes.models import InlineDecision
from apps.minutes.services import add_inline_decision, seed_minutes

User = get_user_model()
UTC = ZoneInfo("UTC")


def _meeting():
    entity = Entity.objects.create(legal_name="CNI Pay")
    return Meeting.objects.create(
        entity=entity, title="Board", starts_at=datetime(2026, 7, 18, 10, 0, tzinfo=UTC)
    )


@pytest.mark.django_db
def test_minutes_seed_from_agenda_and_attendees():
    m = _meeting()
    add_item(meeting=m, title="Item 1", item_type=AgendaItem.ItemType.NOTING)
    add_item(meeting=m, title="Item 2", item_type=AgendaItem.ItemType.APPROVAL)
    u1 = User.objects.create_user(email="d1@cni.test", password="pw-strong-123")
    u2 = User.objects.create_user(email="d2@cni.test", password="pw-strong-123")
    check_in(meeting=m, member=u1)
    check_in(meeting=m, member=u2)

    minutes = seed_minutes(meeting=m)
    assert minutes.blocks.count() == 2       # one per agenda item
    assert minutes.attendees.count() == 2    # auto-populated from present


@pytest.mark.django_db
def test_inline_action_and_resolution_links():
    m = _meeting()
    add_item(meeting=m, title="Accounts", item_type=AgendaItem.ItemType.APPROVAL)
    minutes = seed_minutes(meeting=m)
    block = minutes.blocks.first()

    add_inline_decision(block=block, kind=InlineDecision.Kind.ACTION, text="Follow up with auditors")
    add_inline_decision(block=block, kind=InlineDecision.Kind.RESOLUTION, text="Approve Q3 accounts")

    assert block.inline_decisions.count() == 2
    assert set(block.inline_decisions.values_list("kind", flat=True)) == {"action", "resolution"}
