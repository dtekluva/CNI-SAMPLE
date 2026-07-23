"""
Secure document delivery (FR-DOC-3, NFR-SEC-2).

- View-only documents cannot be downloaded.
- Every rendered/downloaded page is watermarked with the viewer's identity.
- Download links are signed and expire (short-lived).
"""
from django.core.signing import TimestampSigner
from django.utils import timezone

from .models import Document

_signer = TimestampSigner(salt="document-download")


class DownloadNotAllowed(Exception):
    pass


def watermark_for(viewer, at=None):
    """Per-viewer watermark stamped on every page."""
    at = at or timezone.now()
    name = getattr(viewer, "name", "") or viewer.email
    return f"{name} · {viewer.email} · {at:%Y-%m-%d %H:%M UTC}"


def can_download(document):
    return document.access_mode == Document.AccessMode.DOWNLOADABLE


def sign_storage_key(key):
    return _signer.sign(key)


def unsign_storage_key(signed, max_age):
    """Raises SignatureExpired past max_age, BadSignature if tampered."""
    return _signer.unsign(signed, max_age=max_age)


def signed_download_url(storage_key, base="/api/documents/download/"):
    return f"{base}{sign_storage_key(storage_key)}/"


def request_download(document, viewer):
    if not can_download(document):
        raise DownloadNotAllowed("This document is view-only.")
    latest = document.versions.first()
    key = latest.storage_key if latest else ""
    return signed_download_url(key)
