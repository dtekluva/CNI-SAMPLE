from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.entities.models import Entity
from apps.meetings.models import Meeting
from apps.rbac.models import Role
from apps.rbac.services import assign_role

User = get_user_model()


def _setup(mfa_client_factory):
    entity = Entity.objects.create(legal_name="CNI Pay")
    cosec = User.objects.create_user(email="cosec@cni.test", password="pw-strong-123")
    assign_role(actor=cosec, user=cosec, role=Role.COMPANY_SECRETARY, entity=entity)
    meeting = Meeting.objects.create(entity=entity, title="Board", starts_at=timezone.now() + timedelta(days=5))
    return mfa_client_factory(cosec), meeting


@pytest.mark.django_db
def test_agenda_crud_and_reorder(mfa_client_factory):
    client, m = _setup(mfa_client_factory)
    assert client.post(f"/api/meetings/{m.id}/agenda/", {"title": "Item 1", "item_type": "noting"}, format="json").status_code == 201
    assert client.post(f"/api/meetings/{m.id}/agenda/", {"title": "Item 2", "item_type": "approval"}, format="json").status_code == 201

    items = client.get(f"/api/meetings/{m.id}/agenda/").json()
    assert [i["title"] for i in items] == ["Item 1", "Item 2"]

    reordered = client.post(
        f"/api/meetings/{m.id}/agenda/reorder/",
        {"ordered_ids": [items[1]["id"], items[0]["id"]]},
        format="json",
    ).json()
    assert [t["title"] for t in reordered] == ["Item 2", "Item 1"]


@pytest.mark.django_db
def test_toc_endpoint(mfa_client_factory):
    client, m = _setup(mfa_client_factory)
    client.post(f"/api/meetings/{m.id}/agenda/", {"title": "Apologies", "item_type": "noting"}, format="json")
    client.post(f"/api/meetings/{m.id}/agenda/", {"title": "Accounts", "item_type": "approval"}, format="json")
    toc = client.get(f"/api/meetings/{m.id}/toc/").json()
    assert [t["number"] for t in toc] == [1, 2]
    assert [t["title"] for t in toc] == ["Apologies", "Accounts"]
