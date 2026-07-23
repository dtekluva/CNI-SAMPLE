from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from django.contrib.auth import get_user_model

from apps.entities.models import Entity
from apps.meetings.models import Meeting
from apps.meetings.services import generate_series

User = get_user_model()
UTC = ZoneInfo("UTC")


@pytest.mark.django_db
def test_recurring_series_generates_meetings():
    actor = User.objects.create_user(email="cosec@cni.test", password="pw-strong-123")
    entity = Entity.objects.create(legal_name="CNI Pay")
    meetings = generate_series(
        actor=actor,
        entity=entity,
        title="Quarterly Board",
        meeting_type=Meeting.Type.BOARD,
        first_start=datetime(2026, 1, 15, 10, 0, tzinfo=UTC),
        count=4,
        interval_days=90,
    )
    assert len(meetings) == 4
    assert Meeting.objects.filter(entity=entity).count() == 4
    assert (meetings[1].starts_at - meetings[0].starts_at).days == 90


@pytest.mark.django_db
def test_meeting_scoped_to_entity():
    a = Entity.objects.create(legal_name="Entity A")
    b = Entity.objects.create(legal_name="Entity B")
    Meeting.objects.create(entity=a, title="A Board", starts_at=datetime(2026, 3, 1, 9, 0, tzinfo=UTC))
    assert Meeting.objects.filter(entity=a).count() == 1
    assert Meeting.objects.filter(entity=b).count() == 0


@pytest.mark.django_db
def test_timezone_per_invitee():
    entity = Entity.objects.create(legal_name="CNI Pay")
    meeting = Meeting.objects.create(
        entity=entity, title="Board", starts_at=datetime(2026, 7, 18, 14, 0, tzinfo=UTC)
    )
    assert meeting.start_in_tz("Africa/Lagos").hour == 15       # UTC+1
    assert meeting.start_in_tz("America/New_York").hour == 10   # UTC-4 (July)
