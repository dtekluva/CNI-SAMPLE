from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.documents.models import Document
from apps.entities.models import Entity
from apps.meetings.agenda import add_item
from apps.meetings.models import AgendaItem, Meeting
from apps.rbac.models import Role
from apps.rbac.services import assign_role

User = get_user_model()


def _setup(mfa_client_factory):
    entity = Entity.objects.create(legal_name="CNI Pay")
    cosec = User.objects.create_user(email="cosec@cni.test", password="pw-strong-123")
    assign_role(actor=cosec, user=cosec, role=Role.COMPANY_SECRETARY, entity=entity)
    meeting = Meeting.objects.create(entity=entity, title="Board", starts_at=timezone.now() + timedelta(days=5))
    i1 = add_item(meeting=meeting, title="Item 1", item_type=AgendaItem.ItemType.NOTING)
    i2 = add_item(meeting=meeting, title="Item 2", item_type=AgendaItem.ItemType.APPROVAL)
    Document.objects.create(entity=entity, title="Paper A", agenda_item=i1, page_count=3)
    Document.objects.create(entity=entity, title="Paper B", agenda_item=i2, page_count=2)
    return mfa_client_factory(cosec), meeting


@pytest.mark.django_db
def test_compile_pack_api(mfa_client_factory):
    client, m = _setup(mfa_client_factory)
    resp = client.post(f"/api/meetings/{m.id}/pack/")
    assert resp.status_code == 201
    data = resp.json()
    assert data["version"] == 1
    assert data["toc"][0]["page"] == 2 and data["toc"][1]["page"] == 5


@pytest.mark.django_db
def test_pack_toc_api(mfa_client_factory):
    client, m = _setup(mfa_client_factory)
    toc = client.get(f"/api/meetings/{m.id}/pack/").json()["toc"]
    assert [t["title"] for t in toc] == ["Item 1", "Item 2"]
    assert [t["number"] for t in toc] == [1, 2]
