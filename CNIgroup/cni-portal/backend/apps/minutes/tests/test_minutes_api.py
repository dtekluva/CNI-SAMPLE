from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.entities.models import Entity
from apps.meetings.agenda import add_item
from apps.meetings.models import AgendaItem, Meeting
from apps.rbac.models import Role
from apps.rbac.services import assign_role

User = get_user_model()


def _setup(mfa_client_factory, items=2):
    entity = Entity.objects.create(legal_name="CNI Pay")
    cosec = User.objects.create_user(email="cosec@cni.test", password="pw-strong-123")
    assign_role(actor=cosec, user=cosec, role=Role.COMPANY_SECRETARY, entity=entity)
    meeting = Meeting.objects.create(entity=entity, title="Board", starts_at=timezone.now() + timedelta(days=5))
    for i in range(items):
        add_item(meeting=meeting, title=f"Item {i + 1}", item_type=AgendaItem.ItemType.NOTING)
    return mfa_client_factory(cosec), meeting


@pytest.mark.django_db
def test_minutes_seed_api(mfa_client_factory):
    client, m = _setup(mfa_client_factory, items=2)
    resp = client.post(f"/api/meetings/{m.id}/minutes/")
    assert resp.status_code == 201
    data = resp.json()
    assert data["state"] == "draft"
    assert len(data["blocks"]) == 2


@pytest.mark.django_db
def test_minutes_transition_api(mfa_client_factory):
    client, m = _setup(mfa_client_factory)
    client.post(f"/api/meetings/{m.id}/minutes/")
    r = client.post(f"/api/meetings/{m.id}/minutes/transition/", {"to_state": "chairman_review"}, format="json")
    assert r.status_code == 200 and r.json()["state"] == "chairman_review"
    # illegal skip
    bad = client.post(f"/api/meetings/{m.id}/minutes/transition/", {"to_state": "signed"}, format="json")
    assert bad.status_code == 400


@pytest.mark.django_db
def test_comment_blocks_adoption_api(mfa_client_factory):
    client, m = _setup(mfa_client_factory)
    client.post(f"/api/meetings/{m.id}/minutes/")
    client.post(f"/api/meetings/{m.id}/minutes/transition/", {"to_state": "chairman_review"}, format="json")
    client.post(f"/api/meetings/{m.id}/minutes/transition/", {"to_state": "circulated"}, format="json")
    client.post(f"/api/meetings/{m.id}/minutes/comment/", {"text": "typo"}, format="json")
    blocked = client.post(f"/api/meetings/{m.id}/minutes/transition/", {"to_state": "adopted"}, format="json")
    assert blocked.status_code == 409
