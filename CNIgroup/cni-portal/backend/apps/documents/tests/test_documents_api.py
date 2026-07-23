import pytest
from django.contrib.auth import get_user_model

from apps.documents.models import Document
from apps.documents.services import add_version
from apps.entities.models import Entity
from apps.rbac.models import Role
from apps.rbac.services import assign_role

User = get_user_model()


def _director_on(entity, mfa_client_factory):
    u = User.objects.create_user(email="dir@cni.test", password="pw-strong-123")
    assign_role(actor=u, user=u, role=Role.NON_EXECUTIVE_DIRECTOR, entity=entity)
    return mfa_client_factory(u)


@pytest.mark.django_db
def test_documents_scoped(mfa_client_factory):
    a = Entity.objects.create(legal_name="Entity A")
    b = Entity.objects.create(legal_name="Entity B")
    Document.objects.create(entity=a, title="Doc A")
    Document.objects.create(entity=b, title="Doc B")
    titles = [d["title"] for d in _director_on(a, mfa_client_factory).get("/api/documents/").json()]
    assert titles == ["Doc A"]


@pytest.mark.django_db
def test_download_request_blocks_view_only(mfa_client_factory):
    entity = Entity.objects.create(legal_name="CNI Pay")
    doc = Document.objects.create(entity=entity, title="Secret", access_mode=Document.AccessMode.VIEW_ONLY)
    add_version(document=doc, data=b"x", storage_key="k1")
    client = _director_on(entity, mfa_client_factory)

    assert client.get(f"/api/documents/{doc.id}/download/").status_code == 409  # view-only blocked

    doc.access_mode = Document.AccessMode.DOWNLOADABLE
    doc.save()
    resp = client.get(f"/api/documents/{doc.id}/download/")
    assert resp.status_code == 200
    assert "url" in resp.json() and "watermark" in resp.json()


@pytest.mark.django_db
def test_search_scoped(mfa_client_factory):
    a = Entity.objects.create(legal_name="Entity A")
    b = Entity.objects.create(legal_name="Entity B")
    Document.objects.create(entity=a, title="Alpha Secret")
    Document.objects.create(entity=b, title="Beta Secret")
    titles = [d["title"] for d in _director_on(a, mfa_client_factory).get("/api/documents/search/?q=Secret").json()]
    assert titles == ["Alpha Secret"]
