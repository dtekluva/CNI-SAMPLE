from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from django.contrib.auth import get_user_model

from apps.audit.models import AuditEvent
from apps.entities.models import Entity
from apps.meetings.models import Meeting
from apps.minutes.models import Minutes
from apps.minutes.services import seed_minutes
from apps.minutes.workflow import (
    TransitionError,
    UndispositionedComments,
    add_comment,
    dispose_comment,
    transition,
)

User = get_user_model()
UTC = ZoneInfo("UTC")


def _minutes():
    entity = Entity.objects.create(legal_name="CNI Pay")
    meeting = Meeting.objects.create(
        entity=entity, title="Board", starts_at=datetime(2026, 7, 18, 10, 0, tzinfo=UTC)
    )
    return seed_minutes(meeting=meeting)


@pytest.mark.django_db
def test_state_transitions_logged():
    actor = User.objects.create_user(email="cosec@cni.test", password="pw-strong-123")
    minutes = _minutes()
    transition(actor=actor, minutes=minutes, to_state=Minutes.State.CHAIRMAN_REVIEW)
    assert minutes.state == Minutes.State.CHAIRMAN_REVIEW
    assert AuditEvent.objects.filter(action="minutes.state_changed").exists()

    with pytest.raises(TransitionError):
        transition(actor=actor, minutes=minutes, to_state=Minutes.State.SIGNED)  # can't skip


@pytest.mark.django_db
def test_comments_block_adoption_until_dispositioned():
    actor = User.objects.create_user(email="cosec@cni.test", password="pw-strong-123")
    author = User.objects.create_user(email="dir@cni.test", password="pw-strong-123")
    minutes = _minutes()
    transition(actor=actor, minutes=minutes, to_state=Minutes.State.CHAIRMAN_REVIEW)
    transition(actor=actor, minutes=minutes, to_state=Minutes.State.CIRCULATED)

    comment = add_comment(minutes=minutes, author=author, text="Typo in item 3")
    with pytest.raises(UndispositionedComments):
        transition(actor=actor, minutes=minutes, to_state=Minutes.State.ADOPTED)

    dispose_comment(comment=comment)
    transition(actor=actor, minutes=minutes, to_state=Minutes.State.ADOPTED)
    assert minutes.state == Minutes.State.ADOPTED
