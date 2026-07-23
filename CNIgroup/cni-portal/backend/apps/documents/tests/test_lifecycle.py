from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.audit.models import AuditEvent
from apps.documents.models import Annotation, Document, DocumentVersion, OfflinePackGrant
from apps.entities.models import Entity
from apps.meetings.models import Meeting
from apps.rbac.models import Role
from apps.rbac.services import assign_role

User = get_user_model()


@pytest.fixture
def world(db):
    cosec = User.objects.create_user(email="cosec@cni.test", password="pw-strong-123", name="Cosec")
    assign_role(actor=cosec, user=cosec, role=Role.COMPANY_SECRETARY, entity=None)
    entity = Entity.objects.create(legal_name="Alpha", code="AL")
    director = User.objects.create_user(email="dir@cni.test", password="pw-strong-123", name="Ada")
    assign_role(actor=cosec, user=director, role=Role.NON_EXECUTIVE_DIRECTOR, entity=entity)
    return cosec, entity, director


def _doc(entity, **kw):
    d = Document.objects.create(entity=entity, title=kw.pop("title", "Paper"), **kw)
    DocumentVersion.objects.create(document=d, version_number=1, content_hash="a" * 64, text_content="secret text")
    return d


@pytest.mark.django_db
def test_purge_respects_retention_and_legal_hold(world, mfa_client_factory):
    cosec, entity, _ = world
    today = timezone.now().date()
    client = mfa_client_factory(cosec)

    on_hold = _doc(entity, title="Held", retention_until=today - timedelta(days=1), legal_hold=True)
    ripe = _doc(entity, title="Ripe", retention_until=today - timedelta(days=1))
    future = _doc(entity, title="Future", retention_until=today + timedelta(days=30))

    eligible = {d["title"] for d in client.get("/api/documents/purge-eligible/").json()}
    assert eligible == {"Ripe"}  # not held, not future

    # legal hold blocks purge
    assert client.post(f"/api/documents/{on_hold.pk}/purge/").status_code == 409

    # purge the ripe one -> content destroyed, certificate issued, audited
    resp = client.post(f"/api/documents/{ripe.pk}/purge/", {"reason": "end of retention"}, format="json")
    assert resp.status_code == 200 and resp.json()["purged"] is True
    assert resp.json()["certificate"]["reference"].startswith("COD/AL/")
    ripe.refresh_from_db()
    assert ripe.purged and ripe.versions.first().text_content == ""  # content gone
    assert ripe.destruction_certificates.first().content_hash == "a" * 64  # proof preserved
    assert AuditEvent.objects.filter(action="document.purged").exists()


@pytest.mark.django_db
def test_legal_hold_toggle_is_admin_only(world, mfa_client_factory):
    cosec, entity, director = world
    doc = _doc(entity)
    assert mfa_client_factory(director).post(f"/api/documents/{doc.pk}/legal-hold/", {"on": True}, format="json").status_code == 403
    mfa_client_factory(cosec).post(f"/api/documents/{doc.pk}/legal-hold/", {"on": True}, format="json")
    doc.refresh_from_db()
    assert doc.legal_hold is True


@pytest.mark.django_db
def test_offline_pack_grant_wipe_and_sync(world, mfa_client_factory):
    cosec, entity, director = world
    meeting = Meeting.objects.create(entity=entity, title="Q3 Board", starts_at=timezone.now())
    dir_c = mfa_client_factory(director)

    # director takes an offline copy
    g = dir_c.post(f"/api/meetings/{meeting.pk}/offline-pack/", {"device": "iPad-Air"}, format="json").json()
    assert g["status"] == "active"
    # sync before revocation -> no wipe
    assert dir_c.post(f"/api/meetings/{meeting.pk}/offline-pack/sync/").json()["wipe"] is False

    # cosec remote-wipes the meeting's packs
    assert mfa_client_factory(cosec).post(f"/api/meetings/{meeting.pk}/wipe-packs/").json()["revoked"] == 1
    assert AuditEvent.objects.filter(action="offline.pack_wiped").exists()

    # director's next sync is told to wipe, and the grant settles to wiped
    synced = dir_c.post(f"/api/meetings/{meeting.pk}/offline-pack/sync/").json()
    assert synced["wipe"] is True and synced["status"] == "wiped"
    assert OfflinePackGrant.objects.get(meeting=meeting, user=director).status == "wiped"


@pytest.mark.django_db
def test_annotations_private_by_default_and_sharing(world, mfa_client_factory):
    cosec, entity, director = world
    other = User.objects.create_user(email="other@cni.test", password="pw-strong-123", name="Other")
    assign_role(actor=cosec, user=other, role=Role.NON_EXECUTIVE_DIRECTOR, entity=entity)
    doc = _doc(entity)
    dir_c = mfa_client_factory(director)

    # private note — only the author sees it
    dir_c.post("/api/annotations/", {"document": doc.pk, "page": 2, "text": "prep note"}, format="json")
    assert len(dir_c.get(f"/api/annotations/?document={doc.pk}").json()) == 1
    assert len(mfa_client_factory(other).get(f"/api/annotations/?document={doc.pk}").json()) == 0  # no leak

    # shared note — the named recipient sees it
    dir_c.post("/api/annotations/", {"document": doc.pk, "page": 3, "text": "for you",
                                     "visibility": "shared", "shared_with": [other.pk]}, format="json")
    other_view = mfa_client_factory(other).get(f"/api/annotations/?document={doc.pk}").json()
    assert [a["text"] for a in other_view] == ["for you"]
    assert AuditEvent.objects.filter(action="annotation.created").count() == 2
