from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.actions.models import Action
from apps.audit.models import AuditEvent
from apps.entities.models import Entity
from apps.meetings.models import AgendaItem, Meeting
from apps.rbac.models import Role
from apps.rbac.services import assign_role

User = get_user_model()


@pytest.fixture
def cosec(db):
    u = User.objects.create_user(email="cosec-im@cni.test", password="pw-strong-123")
    assign_role(actor=u, user=u, role=Role.COMPANY_SECRETARY, entity=None)
    return u


@pytest.mark.django_db
def test_in_meeting_mode_follow_and_tracker(cosec, mfa_client_factory):
    entity = Entity.objects.create(legal_name="Alpha")
    meeting = Meeting.objects.create(entity=entity, title="Q3", starts_at=timezone.now())
    i1 = AgendaItem.objects.create(meeting=meeting, title="Opening", position=0, time_allocation_minutes=5)
    i2 = AgendaItem.objects.create(meeting=meeting, title="Budget", position=1, time_allocation_minutes=20)
    client = mfa_client_factory(cosec)

    # not live yet
    assert client.get(f"/api/meetings/{meeting.pk}/in-meeting/").json()["active"] is False

    # start -> lands on the first item
    started = client.post(f"/api/meetings/{meeting.pk}/in-meeting/", {"action": "start"}, format="json").json()
    assert started["active"] is True and started["current_item"] == i1.id
    assert AuditEvent.objects.filter(action="meeting.session_started").exists()

    # presenter advances -> followers read the new item + allocation
    now = client.post(f"/api/meetings/{meeting.pk}/in-meeting/", {"action": "present", "item": i2.id}, format="json").json()
    assert now["current_item"] == i2.id and now["allocated_minutes"] == 20 and now["current_position"] == 1

    ended = client.post(f"/api/meetings/{meeting.pk}/in-meeting/", {"action": "end"}, format="json").json()
    assert ended["active"] is False
    assert AuditEvent.objects.filter(action="meeting.session_ended").exists()


@pytest.mark.django_db
def test_group_summary_rolls_up_per_entity(cosec, mfa_client_factory):
    a = Entity.objects.create(legal_name="Alpha")
    b = Entity.objects.create(legal_name="Beta")
    now = timezone.now()
    Meeting.objects.create(entity=a, title="A future", starts_at=now + timedelta(days=5))
    Meeting.objects.create(entity=a, title="A past", starts_at=now - timedelta(days=5))
    Action.objects.create(entity=a, title="overdue", status=Action.Status.OPEN, due_date=(now - timedelta(days=2)).date())
    Action.objects.create(entity=b, title="ok", status=Action.Status.OPEN, due_date=(now + timedelta(days=30)).date())

    data = mfa_client_factory(cosec).get("/api/meetings/group-summary/").json()
    names = {r["entity_name"]: r for r in data["entities"]}
    assert names["Alpha"]["meetings"] == 2 and names["Alpha"]["upcoming"] == 1
    assert names["Alpha"]["overdue_actions"] == 1
    assert data["totals"]["open_actions"] == 2 and data["totals"]["overdue_actions"] == 1


@pytest.mark.django_db
def test_virtual_meeting_fields_exposed(cosec, mfa_client_factory):
    entity = Entity.objects.create(legal_name="Alpha")
    meeting = Meeting.objects.create(
        entity=entity, title="Virtual board", starts_at=timezone.now(), is_virtual=True,
        virtual_link="https://zoom.us/j/123", virtual_provider="Zoom", dial_in="+234 1 000 0000",
    )
    data = mfa_client_factory(cosec).get(f"/api/meetings/{meeting.pk}/").json()
    assert data["virtual_provider"] == "Zoom" and data["dial_in"] == "+234 1 000 0000"
    assert data["virtual_link"] == "https://zoom.us/j/123"
