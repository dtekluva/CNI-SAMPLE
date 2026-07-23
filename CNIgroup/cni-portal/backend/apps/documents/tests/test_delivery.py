import django.core.signing as signing
import pytest
from django.contrib.auth import get_user_model

from apps.documents.delivery import (
    DownloadNotAllowed,
    request_download,
    sign_storage_key,
    unsign_storage_key,
    watermark_for,
)
from apps.documents.models import Document
from apps.documents.services import add_version
from apps.entities.models import Entity

User = get_user_model()


@pytest.mark.django_db
def test_view_only_blocks_download():
    entity = Entity.objects.create(legal_name="CNI Pay")
    viewer = User.objects.create_user(email="dir@cni.test", password="pw-strong-123", name="A Director")
    doc = Document.objects.create(entity=entity, title="Secret", access_mode=Document.AccessMode.VIEW_ONLY)
    add_version(document=doc, data=b"x", storage_key="k1")

    with pytest.raises(DownloadNotAllowed):
        request_download(doc, viewer)

    doc.access_mode = Document.AccessMode.DOWNLOADABLE
    doc.save()
    url = request_download(doc, viewer)
    assert "/api/documents/download/" in url


@pytest.mark.django_db
def test_watermark_contains_viewer_identity():
    viewer = User.objects.create_user(email="dir@cni.test", password="pw-strong-123", name="Ada Director")
    wm = watermark_for(viewer)
    assert "dir@cni.test" in wm
    assert "Ada Director" in wm
    assert "UTC" in wm  # timestamp present


def test_urls_are_signed_and_expire(monkeypatch):
    monkeypatch.setattr(signing.time, "time", lambda: 1000.0)
    signed = sign_storage_key("k1")
    assert unsign_storage_key(signed, max_age=300) == "k1"  # valid immediately

    monkeypatch.setattr(signing.time, "time", lambda: 2000.0)  # 1000s later
    with pytest.raises(signing.SignatureExpired):
        unsign_storage_key(signed, max_age=300)


def test_tampered_url_rejected():
    signed = sign_storage_key("k1")
    with pytest.raises(signing.BadSignature):
        unsign_storage_key(signed + "x", max_age=300)
