import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.audit.models import AuditEvent
from apps.entities.models import Entity
from apps.meetings.models import AgendaItem, Meeting
from apps.minutes.models import Minutes
from apps.rbac.models import Role
from apps.rbac.services import assign_role

User = get_user_model()


@pytest.mark.django_db
def test_block_text_editable_until_adopted_then_locked(mfa_client_factory):
    cosec = User.objects.create_user(email="cosec@cni.test", password="pw-strong-123")
    assign_role(actor=cosec, user=cosec, role=Role.COMPANY_SECRETARY, entity=None)
    entity = Entity.objects.create(legal_name="Alpha")
    meeting = Meeting.objects.create(entity=entity, title="Q3 Board", starts_at=timezone.now())
    AgendaItem.objects.create(meeting=meeting, title="Budget approval", position=1)
    client = mfa_client_factory(cosec)

    body = client.get(f"/api/meetings/{meeting.pk}/minutes/").json()
    block = body["blocks"][0]
    assert block["agenda_item_title"] == "Budget approval"  # titles now in payload

    resp = client.post(
        f"/api/meetings/{meeting.pk}/minutes/block/",
        {"block": block["id"], "text": "The budget was approved."},
        format="json",
    )
    assert resp.status_code == 200 and resp.json()["text"] == "The budget was approved."
    assert AuditEvent.objects.filter(action="minutes.block.updated").exists()

    Minutes.objects.filter(meeting=meeting).update(state=Minutes.State.ADOPTED)
    locked = client.post(
        f"/api/meetings/{meeting.pk}/minutes/block/", {"block": block["id"], "text": "tamper"}, format="json"
    )
    assert locked.status_code == 409  # the adopted record is immutable

    unknown = client.post(f"/api/meetings/{meeting.pk}/minutes/block/", {"block": 99999, "text": "x"}, format="json")
    assert unknown.status_code == 404
