from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from django.contrib.auth import get_user_model

from apps.audit.models import AuditEvent
from apps.entities.models import Entity
from apps.resolutions.ctc import CTCNotAllowed, generate_ctc
from apps.resolutions.models import Resolution
from apps.resolutions.services import create_resolution

User = get_user_model()
UTC = ZoneInfo("UTC")
WHEN = datetime(2026, 7, 1, 10, 0, tzinfo=UTC)


@pytest.mark.django_db
def test_ctc_only_for_passed_resolution():
    entity = Entity.objects.create(legal_name="CNI Pay", code="CNI", cac_rc_number="RC123456")
    cosec = User.objects.create_user(email="cosec@cni.test", password="pw-strong-123", name="Ada Cosec")
    r = create_resolution(entity=entity, title="Open account", text="Resolved that...", when=WHEN)

    with pytest.raises(CTCNotAllowed):
        generate_ctc(resolution=r, issued_by=cosec)  # PENDING

    r.outcome = Resolution.Outcome.PASSED
    r.save(update_fields=["outcome"])
    ctc = generate_ctc(resolution=r, issued_by=cosec)

    assert "CNI Pay" in ctc.body
    assert "RC123456" in ctc.body
    assert "CERTIFIED TRUE COPY" in ctc.body
    assert r.number in ctc.body
    assert "Company Secretary" in ctc.body


@pytest.mark.django_db
def test_ctc_logged_as_issued():
    entity = Entity.objects.create(legal_name="CNI Pay", code="CNI", cac_rc_number="RC1")
    cosec = User.objects.create_user(email="cosec@cni.test", password="pw-strong-123")
    r = create_resolution(entity=entity, title="R", text="x", when=WHEN)
    r.outcome = Resolution.Outcome.PASSED
    r.save(update_fields=["outcome"])
    generate_ctc(resolution=r, issued_by=cosec)
    assert AuditEvent.objects.filter(action="ctc.issued").exists()
