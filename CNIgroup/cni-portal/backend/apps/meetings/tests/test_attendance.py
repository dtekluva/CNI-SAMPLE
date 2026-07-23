from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from django.contrib.auth import get_user_model

from apps.entities.models import Entity
from apps.meetings.attendance import attendance_stats, check_in, quorum_status, record_apology
from apps.meetings.models import Attendance, Meeting

User = get_user_model()
UTC = ZoneInfo("UTC")


def _meeting(quorum=0):
    entity = Entity.objects.create(legal_name="CNI Pay")
    return Meeting.objects.create(
        entity=entity, title="Board", starts_at=datetime(2026, 7, 18, 10, 0, tzinfo=UTC), quorum=quorum
    )


def _user(n):
    return User.objects.create_user(email=f"d{n}@cni.test", password="pw-strong-123")


@pytest.mark.django_db
def test_quorum_met_indicator():
    m = _meeting(quorum=3)
    check_in(meeting=m, member=_user(1))
    check_in(meeting=m, member=_user(2))
    assert quorum_status(m)["met"] is False  # 2 < 3

    check_in(meeting=m, member=_user(3))
    status = quorum_status(m)
    assert status["present"] == 3 and status["met"] is True


@pytest.mark.django_db
def test_apologies_recorded():
    m = _meeting(quorum=1)
    u = _user(1)
    record_apology(meeting=m, member=u)
    att = Attendance.objects.get(meeting=m, member=u)
    assert att.status == Attendance.Status.APOLOGY
    assert quorum_status(m)["present"] == 0  # apology is not present


@pytest.mark.django_db
def test_attendance_stats_persist():
    u = _user(1)
    m1, m2 = _meeting(), _meeting()
    check_in(meeting=m1, member=u)
    record_apology(meeting=m2, member=u)
    stats = attendance_stats(u)
    assert stats == {"meetings": 2, "present": 1, "apologies": 1}
