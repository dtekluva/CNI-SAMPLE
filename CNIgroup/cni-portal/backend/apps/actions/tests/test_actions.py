from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest
from django.contrib.auth import get_user_model

from apps.actions.models import Action
from apps.actions.services import complete_action, create_action
from apps.entities.models import Entity
from apps.meetings.agenda import add_item
from apps.meetings.models import AgendaItem, Meeting

User = get_user_model()
UTC = ZoneInfo("UTC")


@pytest.mark.django_db
def test_action_has_owner_due_and_source_link():
    entity = Entity.objects.create(legal_name="CNI Pay")
    meeting = Meeting.objects.create(
        entity=entity, title="Board", starts_at=datetime(2026, 7, 18, 10, 0, tzinfo=UTC)
    )
    item = add_item(meeting=meeting, title="Accounts", item_type=AgendaItem.ItemType.APPROVAL)
    owner = User.objects.create_user(email="dir@cni.test", password="pw-strong-123")

    action = create_action(
        entity=entity, title="Follow up with auditors", owner=owner,
        due_date=date(2026, 8, 1), meeting=meeting, agenda_item=item,
    )
    assert action.owner == owner
    assert action.due_date == date(2026, 8, 1)
    assert action.agenda_item == item  # source link


@pytest.mark.django_db
def test_action_owner_can_be_non_member():
    entity = Entity.objects.create(legal_name="CNI Pay")
    action = create_action(entity=entity, title="CFO to send report", owner_name="Emeka (CFO)")
    assert action.owner is None
    assert action.owner_name == "Emeka (CFO)"


@pytest.mark.django_db
def test_action_completion():
    entity = Entity.objects.create(legal_name="CNI Pay")
    action = create_action(entity=entity, title="Task")
    complete_action(action=action, evidence="Done, see email")
    action.refresh_from_db()
    assert action.status == Action.Status.DONE
    assert action.evidence == "Done, see email"
