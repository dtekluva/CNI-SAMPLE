import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.audit.models import AuditEvent
from apps.entities.models import Entity
from apps.meetings.models import AgendaItem, Meeting
from apps.minutes.models import MinuteBlock, Minutes
from apps.minutes.services import compute_minutes_hash
from apps.minutes.workflow import transition
from apps.rbac.models import Role
from apps.rbac.services import assign_role

User = get_user_model()


def _signed_minutes(entity, cosec, title="Q1 Board"):
    meeting = Meeting.objects.create(entity=entity, title=title, starts_at=timezone.now())
    item = AgendaItem.objects.create(meeting=meeting, title="Budget", position=1)
    minutes = Minutes.objects.create(meeting=meeting)
    MinuteBlock.objects.create(minutes=minutes, agenda_item=item, text="The budget was approved.")
    minutes.attendees.set([cosec])
    for to in ["chairman_review", "circulated", "adopted", "signed"]:
        transition(actor=cosec, minutes=minutes, to_state=to)
    minutes.refresh_from_db()
    return meeting, minutes


@pytest.fixture
def cosec(db):
    u = User.objects.create_user(email="cosec@cni.test", password="pw-strong-123", name="Cosec")
    assign_role(actor=u, user=u, role=Role.COMPANY_SECRETARY, entity=None)
    return u


@pytest.mark.django_db
def test_signing_seals_minutes_with_hash_and_signer(cosec):
    entity = Entity.objects.create(legal_name="Alpha")
    _, minutes = _signed_minutes(entity, cosec)
    assert minutes.state == "signed"
    assert len(minutes.content_hash) == 64
    assert minutes.signed_by == cosec and minutes.signed_at is not None
    assert AuditEvent.objects.filter(action="minutes.signed").exists()


@pytest.mark.django_db
def test_minute_book_lists_signed_chronologically_and_pdf(cosec, mfa_client_factory):
    entity = Entity.objects.create(legal_name="Alpha")
    _, m1 = _signed_minutes(entity, cosec, "Q1 Board")
    # a draft (unsigned) meeting must NOT appear in the book
    draft_meeting = Meeting.objects.create(entity=entity, title="Q2 Draft", starts_at=timezone.now())
    Minutes.objects.create(meeting=draft_meeting)
    client = mfa_client_factory(cosec)

    book = client.get(f"/api/minute-book/?entity={entity.pk}").json()
    assert [b["meeting_title"] for b in book] == ["Q1 Board"]  # only the signed one
    assert book[0]["content_hash"] and book[0]["signed_by_name"] == "Cosec"

    pdf = client.get(f"/api/minute-book/{m1.pk}/pdf/")
    assert pdf.status_code == 200 and pdf["Content-Type"] == "application/pdf"
    assert bytes(pdf.content[:5]) == b"%PDF-"
    assert AuditEvent.objects.filter(action="minutebook.exported").exists()


@pytest.mark.django_db
def test_tamper_verify_detects_alteration(cosec, mfa_client_factory):
    entity = Entity.objects.create(legal_name="Alpha")
    _, minutes = _signed_minutes(entity, cosec)
    client = mfa_client_factory(cosec)

    ok = client.get(f"/api/minute-book/{minutes.pk}/verify/").json()
    assert ok["intact"] is True and ok["stored"] == ok["current"]

    # tamper with a sealed block directly in the DB — verify must catch it
    block = minutes.blocks.first()
    block.text = "The budget was REJECTED."
    block.save(update_fields=["text"])
    bad = client.get(f"/api/minute-book/{minutes.pk}/verify/").json()
    assert bad["intact"] is False and bad["stored"] != bad["current"]


@pytest.mark.django_db
def test_minute_book_is_entity_scoped(cosec, mfa_client_factory):
    a = Entity.objects.create(legal_name="Alpha")
    b = Entity.objects.create(legal_name="Beta")
    _signed_minutes(a, cosec, "Alpha AGM")
    _, m_beta = _signed_minutes(b, cosec, "Beta Board")

    director = User.objects.create_user(email="dir@cni.test", password="pw-strong-123")
    assign_role(actor=cosec, user=director, role=Role.NON_EXECUTIVE_DIRECTOR, entity=a)
    dc = mfa_client_factory(director)
    titles = [x["meeting_title"] for x in dc.get("/api/minute-book/").json()]
    assert titles == ["Alpha AGM"]  # no leak of Beta's minute book
    assert dc.get(f"/api/minute-book/{m_beta.pk}/pdf/").status_code == 404
