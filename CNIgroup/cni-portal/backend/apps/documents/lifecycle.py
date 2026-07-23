"""
Document lifecycle (FR-DOC-5/6): retention, legal hold, secure purge, and
offline-pack revocation. Purge is destructive but recorded — a certificate of
destruction preserves proof of *what* was destroyed (title + content hash)
without keeping the content itself.
"""
from django.utils import timezone

from apps.audit.models import AuditEvent

from .models import DestructionCertificate, Document, OfflinePackGrant


def purge_eligible(queryset=None, on_date=None):
    """Documents past retention, not under legal hold, not already purged."""
    on_date = on_date or timezone.now().date()
    qs = queryset if queryset is not None else Document.objects.all()
    return qs.filter(purged=False, legal_hold=False, retention_until__isnull=False, retention_until__lte=on_date)


def purge_document(*, document, actor=None, reason=""):
    """Securely purge a document: clear content, mark purged, issue a certificate."""
    if document.legal_hold:
        raise ValueError("Document is under legal hold and cannot be purged.")
    if document.purged:
        return document.destruction_certificates.first()

    last = document.versions.first()
    content_hash = last.content_hash if last else ""

    # destroy the content on every version, keep the row shells
    document.versions.update(storage_key="", text_content="")

    ref = f"COD/{document.entity.code or 'CNI'}/{timezone.now():%Y%m%d}/{document.pk}"
    cert = DestructionCertificate.objects.create(
        document=document,
        reference=ref,
        title_at_destruction=document.title,
        content_hash=content_hash,
        reason=reason,
        certified_by=actor,
    )
    document.purged = True
    document.purged_at = timezone.now()
    document.save(update_fields=["purged", "purged_at"])
    AuditEvent.objects.record(
        action="document.purged", actor=actor, target=document,
        metadata={"certificate": ref, "reason": reason},
    )
    return cert


def set_legal_hold(*, document, on, actor=None):
    document.legal_hold = on
    document.save(update_fields=["legal_hold"])
    AuditEvent.objects.record(
        action="document.legal_hold_set" if on else "document.legal_hold_released",
        actor=actor, target=document,
    )
    return document


def wipe_meeting_packs(*, meeting, actor=None):
    """Revoke every active offline copy of a meeting's pack (FR-DOC-6 remote wipe)."""
    grants = meeting.offline_grants.filter(status=OfflinePackGrant.Status.ACTIVE)
    n = grants.count()
    grants.update(status=OfflinePackGrant.Status.REVOKED, revoked_at=timezone.now())
    AuditEvent.objects.record(
        action="offline.pack_wiped", actor=actor, target=meeting, metadata={"grants_revoked": n},
    )
    return n
