from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.audit.models import AuditEvent
from apps.entities.models import Entity
from apps.resolutions.circular import circulate, lapse_if_expired, sign
from apps.resolutions.models import Resolution
from apps.resolutions.services import create_resolution

User = get_user_model()
UTC = ZoneInfo("UTC")
WHEN = datetime(2026, 7, 1, 10, 0, tzinfo=UTC)


def _circular(entity, threshold, expires_at):
    r = create_resolution(entity=entity, title="Open bank account", text="...", when=WHEN)
    return circulate(resolution=r, threshold=threshold, expires_at=expires_at)


@pytest.mark.django_db
def test_effective_on_threshold():
    entity = Entity.objects.create(legal_name="CNI Pay", code="CNI")
    u1 = User.objects.create_user(email="d1@cni.test", password="pw-strong-123")
    u2 = User.objects.create_user(email="d2@cni.test", password="pw-strong-123")
    r = _circular(entity, threshold=2, expires_at=timezone.now() + timedelta(days=7))

    sign(resolution=r, signer=u1)
    r.refresh_from_db()
    assert r.outcome == Resolution.Outcome.PENDING  # 1 of 2

    sign(resolution=r, signer=u2)
    r.refresh_from_db()
    assert r.outcome == Resolution.Outcome.PASSED
    assert r.effective_date is not None


@pytest.mark.django_db
def test_expiry_lapses():
    entity = Entity.objects.create(legal_name="CNI Pay", code="CNI")
    r = _circular(entity, threshold=3, expires_at=timezone.now() - timedelta(days=1))
    lapse_if_expired(resolution=r, as_of=timezone.now())
    r.refresh_from_db()
    assert r.outcome == Resolution.Outcome.LAPSED


@pytest.mark.django_db
def test_signature_events_audited():
    entity = Entity.objects.create(legal_name="CNI Pay", code="CNI")
    u1 = User.objects.create_user(email="d1@cni.test", password="pw-strong-123")
    r = _circular(entity, threshold=2, expires_at=timezone.now() + timedelta(days=7))
    sign(resolution=r, signer=u1)
    assert AuditEvent.objects.filter(action="resolution.circulated").exists()
    assert AuditEvent.objects.filter(action="resolution.signed").exists()
