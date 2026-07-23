from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.documents.models import Document
from apps.documents.pdf import render_pack_pdf
from apps.entities.models import Entity
from apps.meetings.agenda import add_item
from apps.meetings.models import AgendaItem, Meeting
from apps.rbac.models import Role
from apps.rbac.services import assign_role

User = get_user_model()


def _meeting():
    entity = Entity.objects.create(legal_name="CNI Pay")
    meeting = Meeting.objects.create(entity=entity, title="Board", starts_at=timezone.now() + timedelta(days=5))
    i1 = add_item(meeting=meeting, title="Item 1", item_type=AgendaItem.ItemType.NOTING)
    Document.objects.create(entity=entity, title="Paper A", agenda_item=i1, page_count=2)
    return entity, meeting


@pytest.mark.django_db
def test_pack_pdf_bytes_and_watermark():
    _, meeting = _meeting()
    pdf_wm = render_pack_pdf(meeting=meeting, watermark="Ada Director · ada@cni.test · 2026-07-17")
    pdf_no = render_pack_pdf(meeting=meeting, watermark="")
    assert pdf_wm[:4] == b"%PDF"
    assert len(pdf_wm) > len(pdf_no)  # watermark adds content to every page


@pytest.mark.django_db
def test_pack_pdf_endpoint(mfa_client_factory):
    entity, meeting = _meeting()
    cosec = User.objects.create_user(email="cosec@cni.test", password="pw-strong-123")
    assign_role(actor=cosec, user=cosec, role=Role.COMPANY_SECRETARY, entity=entity)
    resp = mfa_client_factory(cosec).get(f"/api/meetings/{meeting.id}/pack-pdf/")
    assert resp.status_code == 200
    assert resp["Content-Type"] == "application/pdf"
    assert resp.content[:4] == b"%PDF"
