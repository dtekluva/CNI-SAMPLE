from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from apps.entities.models import Entity
from apps.meetings.agenda import add_item, reorder_items, table_of_contents
from apps.meetings.models import AgendaItem, Meeting

UTC = ZoneInfo("UTC")


def _meeting():
    entity = Entity.objects.create(legal_name="CNI Pay")
    return Meeting.objects.create(
        entity=entity, title="Board", starts_at=datetime(2026, 7, 18, 10, 0, tzinfo=UTC)
    )


@pytest.mark.django_db
def test_reorder_renumbers_and_updates_toc():
    m = _meeting()
    a = add_item(meeting=m, title="Apologies", item_type=AgendaItem.ItemType.NOTING)
    b = add_item(meeting=m, title="Minutes", item_type=AgendaItem.ItemType.APPROVAL)
    c = add_item(meeting=m, title="Accounts", item_type=AgendaItem.ItemType.APPROVAL)

    toc = table_of_contents(m)
    assert [t["title"] for t in toc] == ["Apologies", "Minutes", "Accounts"]
    assert [t["number"] for t in toc] == [1, 2, 3]

    reorder_items(meeting=m, ordered_ids=[c.id, a.id, b.id])
    toc = table_of_contents(m)
    assert [t["title"] for t in toc] == ["Accounts", "Apologies", "Minutes"]
    assert [t["number"] for t in toc] == [1, 2, 3]


@pytest.mark.django_db
def test_item_types_persist():
    m = _meeting()
    item = add_item(meeting=m, title="Approve accounts", item_type=AgendaItem.ItemType.APPROVAL)
    item.refresh_from_db()
    assert item.item_type == "approval"
    assert item.get_item_type_display() == "For Approval"
