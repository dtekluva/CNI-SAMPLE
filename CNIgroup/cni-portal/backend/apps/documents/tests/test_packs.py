from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from django.contrib.auth import get_user_model

from apps.audit.models import AuditEvent
from apps.documents.models import Document
from apps.documents.packs import compile_pack
from apps.entities.models import Entity
from apps.meetings.agenda import add_item
from apps.meetings.models import AgendaItem, Meeting

User = get_user_model()
UTC = ZoneInfo("UTC")


def _setup():
    actor = User.objects.create_user(email="cosec@cni.test", password="pw-strong-123")
    entity = Entity.objects.create(legal_name="CNI Pay")
    meeting = Meeting.objects.create(
        entity=entity, title="Board", starts_at=datetime(2026, 7, 18, 10, 0, tzinfo=UTC)
    )
    return actor, entity, meeting


@pytest.mark.django_db
def test_pack_toc_maps_items_to_pages():
    actor, entity, meeting = _setup()
    i1 = add_item(meeting=meeting, title="Item 1", item_type=AgendaItem.ItemType.NOTING)
    i2 = add_item(meeting=meeting, title="Item 2", item_type=AgendaItem.ItemType.APPROVAL)
    Document.objects.create(entity=entity, title="Paper A", agenda_item=i1, page_count=3)
    Document.objects.create(entity=entity, title="Paper B", agenda_item=i2, page_count=2)

    result = compile_pack(meeting=meeting, actor=actor)
    toc = result["toc"]
    assert toc[0]["title"] == "Item 1" and toc[0]["page"] == 2   # after the cover
    assert toc[1]["title"] == "Item 2" and toc[1]["page"] == 5   # cover + 3 pages


@pytest.mark.django_db
def test_republish_increments_version_and_notifies():
    actor, entity, meeting = _setup()
    r1 = compile_pack(meeting=meeting, actor=actor)
    r2 = compile_pack(meeting=meeting, actor=actor)
    assert r1["pack"].version_number == 1
    assert r2["pack"].version_number == 2
    assert AuditEvent.objects.filter(action="pack.published").exists()
    assert AuditEvent.objects.filter(action="pack.republished").exists()


@pytest.mark.django_db
def test_late_paper_flagged():
    actor, entity, meeting = _setup()
    i1 = add_item(meeting=meeting, title="Item 1", item_type=AgendaItem.ItemType.NOTING)
    Document.objects.create(entity=entity, title="Late paper", agenda_item=i1, page_count=1, is_late=True)
    result = compile_pack(meeting=meeting, actor=actor)
    flagged = any(p["late"] for item in result["toc"] for p in item["papers"])
    assert flagged
