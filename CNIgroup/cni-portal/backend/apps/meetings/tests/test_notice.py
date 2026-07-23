from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.audit.models import AuditEvent
from apps.entities.models import Entity
from apps.meetings.models import Meeting
from apps.meetings.notice import (
    ShortNoticeError,
    dispatch_notice,
    record_consent_to_short_notice,
)

User = get_user_model()


@pytest.mark.django_db
def test_short_notice_requires_consent():
    actor = User.objects.create_user(email="cosec@cni.test", password="pw-strong-123")
    u1 = User.objects.create_user(email="d1@cni.test", password="pw-strong-123")
    u2 = User.objects.create_user(email="d2@cni.test", password="pw-strong-123")
    entity = Entity.objects.create(legal_name="CNI Pay")
    meeting = Meeting.objects.create(
        entity=entity, title="Urgent Board", starts_at=timezone.now() + timedelta(days=2)
    )

    with pytest.raises(ShortNoticeError):
        dispatch_notice(actor=actor, meeting=meeting, recipients=[u1, u2])

    record_consent_to_short_notice(actor=actor, meeting=meeting, member=u1)
    record_consent_to_short_notice(actor=actor, meeting=meeting, member=u2)
    proofs = dispatch_notice(actor=actor, meeting=meeting, recipients=[u1, u2])
    assert len(proofs) == 2


@pytest.mark.django_db
def test_notice_dispatch_proof_audited():
    actor = User.objects.create_user(email="cosec@cni.test", password="pw-strong-123")
    u1 = User.objects.create_user(email="d1@cni.test", password="pw-strong-123")
    entity = Entity.objects.create(legal_name="CNI Pay")
    meeting = Meeting.objects.create(
        entity=entity, title="Board", starts_at=timezone.now() + timedelta(days=30)
    )
    dispatch_notice(actor=actor, meeting=meeting, recipients=[u1])
    assert AuditEvent.objects.filter(action="notice.dispatched").count() == 1
