import pytest
from django.contrib.auth import get_user_model

from apps.announcements.models import Announcement
from apps.audit.models import AuditEvent
from apps.entities.models import Entity
from apps.rbac.models import Role
from apps.rbac.services import assign_role

User = get_user_model()


@pytest.fixture
def world(db):
    cosec = User.objects.create_user(email="cosec-an@cni.test", password="pw-strong-123", name="Cosec")
    assign_role(actor=cosec, user=cosec, role=Role.COMPANY_SECRETARY, entity=None)
    entity = Entity.objects.create(legal_name="Alpha")
    director = User.objects.create_user(email="dir-an@cni.test", password="pw-strong-123", name="Ada")
    assign_role(actor=cosec, user=director, role=Role.NON_EXECUTIVE_DIRECTOR, entity=entity)
    return cosec, entity, director


@pytest.mark.django_db
def test_post_read_and_receipts(world, mfa_client_factory):
    cosec, entity, director = world
    posted = mfa_client_factory(cosec).post(
        "/api/announcements/", {"entity": entity.pk, "title": "Board circular Q3", "body": "Please review."}, format="json"
    )
    assert posted.status_code == 201
    aid = posted.json()["id"]
    assert AuditEvent.objects.filter(action="announcement.posted").exists()

    # director cannot post
    denied = mfa_client_factory(director).post(
        "/api/announcements/", {"entity": entity.pk, "title": "X", "body": "y"}, format="json")
    assert denied.status_code == 403

    # director reads -> receipt recorded
    dir_client = mfa_client_factory(director)
    assert dir_client.get("/api/announcements/").json()[0]["read_by_me"] is False
    dir_client.post(f"/api/announcements/{aid}/read/")
    assert dir_client.get("/api/announcements/").json()[0]["read_by_me"] is True

    # leadership sees the receipt; a director cannot
    receipts = mfa_client_factory(cosec).get(f"/api/announcements/{aid}/receipts/").json()
    assert any(r["name"] == "Ada" for r in receipts)
    assert mfa_client_factory(director).get(f"/api/announcements/{aid}/receipts/").status_code == 403


@pytest.mark.django_db
def test_announcements_are_scoped(world, mfa_client_factory):
    cosec, entity, director = world
    other = Entity.objects.create(legal_name="Beta")
    Announcement.objects.create(entity=entity, title="Mine", body="x", posted_by=cosec)
    Announcement.objects.create(entity=other, title="Beta secret", body="y", posted_by=cosec)
    titles = [a["title"] for a in mfa_client_factory(director).get("/api/announcements/").json()]
    assert titles == ["Mine"]
