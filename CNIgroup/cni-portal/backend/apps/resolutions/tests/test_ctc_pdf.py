from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from django.contrib.auth import get_user_model

from apps.documents.pdf import render_ctc_pdf
from apps.entities.models import Entity
from apps.rbac.models import Role
from apps.rbac.services import assign_role
from apps.resolutions.ctc import generate_ctc
from apps.resolutions.models import Resolution
from apps.resolutions.services import create_resolution

User = get_user_model()
WHEN = datetime(2026, 7, 1, 10, 0, tzinfo=ZoneInfo("UTC"))


@pytest.mark.django_db
def test_ctc_pdf_bytes():
    entity = Entity.objects.create(legal_name="CNI Pay", code="CNI", cac_rc_number="RC1")
    cosec = User.objects.create_user(email="cosec@cni.test", password="pw-strong-123")
    r = create_resolution(entity=entity, title="Open account", text="Resolved...", when=WHEN)
    r.outcome = Resolution.Outcome.PASSED
    r.save(update_fields=["outcome"])
    ctc = generate_ctc(resolution=r, issued_by=cosec)

    pdf = render_ctc_pdf(ctc=ctc)
    assert pdf[:4] == b"%PDF"
    assert len(pdf) > 500


@pytest.mark.django_db
def test_ctc_pdf_endpoint(mfa_client_factory):
    entity = Entity.objects.create(legal_name="CNI Pay", code="CNI", cac_rc_number="RC1")
    cosec = User.objects.create_user(email="cosec@cni.test", password="pw-strong-123")
    assign_role(actor=cosec, user=cosec, role=Role.COMPANY_SECRETARY, entity=entity)
    r = create_resolution(entity=entity, title="Open account", text="x", when=WHEN)
    client = mfa_client_factory(cosec)

    assert client.get(f"/api/resolutions/{r.id}/ctc-pdf/").status_code == 409  # not passed

    r.outcome = Resolution.Outcome.PASSED
    r.save(update_fields=["outcome"])
    resp = client.get(f"/api/resolutions/{r.id}/ctc-pdf/")
    assert resp.status_code == 200 and resp["Content-Type"] == "application/pdf"
    assert resp.content[:4] == b"%PDF"
