from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.actions.models import Action
from apps.entities.models import Entity
from apps.meetings.models import AgendaItem, Meeting
from apps.rbac.models import Role
from apps.rbac.services import assign_role

User = get_user_model()


@pytest.mark.django_db
def test_matters_arising_carries_open_prior_actions(mfa_client_factory):
    cosec = User.objects.create_user(email="cosec-ma@cni.test", password="pw-strong-123")
    assign_role(actor=cosec, user=cosec, role=Role.COMPANY_SECRETARY, entity=None)
    entity = Entity.objects.create(legal_name="Alpha")
    now = timezone.now()

    prior = Meeting.objects.create(entity=entity, title="Q1 Board", starts_at=now - timedelta(days=90))
    nxt = Meeting.objects.create(entity=entity, title="Q2 Board", starts_at=now + timedelta(days=7))
    AgendaItem.objects.create(meeting=nxt, title="Opening & apologies", position=0)

    Action.objects.create(entity=entity, meeting=prior, title="FX sensitivity analysis", status=Action.Status.OPEN)
    Action.objects.create(entity=entity, meeting=prior, title="Done thing", status=Action.Status.DONE)
    Action.objects.create(entity=entity, meeting=nxt, title="This meeting's own action", status=Action.Status.OPEN)

    client = mfa_client_factory(cosec)

    # GET previews without mutating the agenda
    preview = client.get(f"/api/meetings/{nxt.pk}/matters-arising/").json()
    assert [a["title"] for a in preview["actions"]] == ["FX sensitivity analysis"]  # open + prior only
    assert preview["on_agenda"] is False
    assert not nxt.agenda_items.filter(title="Matters arising").exists()

    # POST plants the item right after the opening item
    result = client.post(f"/api/meetings/{nxt.pk}/matters-arising/").json()
    assert result["on_agenda"] is True
    item = nxt.agenda_items.get(title="Matters arising")
    assert item.position == 1

    # idempotent — no duplicate item on repeat POST
    client.post(f"/api/meetings/{nxt.pk}/matters-arising/")
    assert nxt.agenda_items.filter(title="Matters arising").count() == 1
