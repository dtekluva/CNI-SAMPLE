"""
Document library & versioning (FR-DOC-1, FR-DOC-2). Documents are entity-scoped
(access inherits from the entity), organised by committee/meeting/topic, and
versioned with a content hash per version. Watermark/download control is T-D2.
"""
from django.conf import settings
from django.db import models


class Document(models.Model):
    class AccessMode(models.TextChoices):
        VIEW_ONLY = "view_only", "View only"
        DOWNLOADABLE = "downloadable", "Downloadable"

    entity = models.ForeignKey("entities.Entity", on_delete=models.CASCADE, related_name="documents")
    title = models.CharField(max_length=255)
    access_mode = models.CharField(
        max_length=16, choices=AccessMode.choices, default=AccessMode.VIEW_ONLY
    )
    committee = models.CharField(max_length=128, blank=True, default="")
    topic = models.CharField(max_length=128, blank=True, default="")
    meeting = models.ForeignKey(
        "meetings.Meeting", null=True, blank=True, on_delete=models.SET_NULL, related_name="documents"
    )
    agenda_item = models.ForeignKey(
        "meetings.AgendaItem", null=True, blank=True, on_delete=models.SET_NULL, related_name="papers"
    )
    page_count = models.PositiveIntegerField(default=1)
    is_late = models.BooleanField(default=False, help_text="Supplementary/late paper")
    # --- lifecycle (FR-DOC-5, NDPA) ---
    retention_until = models.DateField(
        null=True, blank=True, help_text="End of retention; eligible for purge after this date"
    )
    legal_hold = models.BooleanField(
        default=False, help_text="Under legal hold — purge is blocked regardless of retention"
    )
    purged = models.BooleanField(default=False)
    purged_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return self.title


class BoardPack(models.Model):
    """A compiled, versioned board pack for a meeting (FR-MTG-4)."""

    meeting = models.ForeignKey("meetings.Meeting", on_delete=models.CASCADE, related_name="board_packs")
    version_number = models.PositiveIntegerField()
    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    published_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("meeting", "version_number")
        ordering = ("-version_number",)

    def __str__(self):
        return f"{self.meeting.title} pack v{self.version_number}"


class DocumentVersion(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="versions")
    version_number = models.PositiveIntegerField()
    content_hash = models.CharField(max_length=64)
    storage_key = models.CharField(max_length=512, blank=True, default="")
    text_content = models.TextField(blank=True, default="")  # extracted/OCR text for search
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("document", "version_number")
        ordering = ("-version_number",)

    def __str__(self):
        return f"{self.document.title} v{self.version_number}"


class DestructionCertificate(models.Model):
    """Certificate of destruction recorded when a document is purged (FR-DOC-5, NDPA)."""

    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="destruction_certificates")
    reference = models.CharField(max_length=80)
    title_at_destruction = models.CharField(max_length=255)
    content_hash = models.CharField(max_length=64, blank=True, default="", help_text="Hash of the last version — proof of what was destroyed")
    reason = models.CharField(max_length=255, blank=True, default="")
    certified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    certified_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.reference


class OfflinePackGrant(models.Model):
    """
    A director's offline copy of a meeting's pack (FR-DOC-6). Modelled server-side
    as a grant record: it can be revoked (or wiped when the pack is superseded),
    and the next device sync honours the revocation — the local copy is wiped.
    """

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        REVOKED = "revoked", "Revoked (wipe on next sync)"
        WIPED = "wiped", "Wiped"

    meeting = models.ForeignKey("meetings.Meeting", on_delete=models.CASCADE, related_name="offline_grants")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="offline_grants")
    device = models.CharField(max_length=128, blank=True, default="")
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.ACTIVE)
    granted_at = models.DateTimeField(auto_now_add=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    synced_at = models.DateTimeField(null=True, blank=True, help_text="Last device sync that acknowledged status")

    class Meta:
        ordering = ("-granted_at",)

    def __str__(self):
        return f"{self.user} · {self.meeting} pack ({self.status})"


class Annotation(models.Model):
    """
    A director's note on a paper (FR-DOC-4). Private by default; may be shared
    with named recipients. Anchored to a page so it can re-map when a pack is
    republished (shift-flagging is a later enhancement).
    """

    class Visibility(models.TextChoices):
        PRIVATE = "private", "Private"
        SHARED = "shared", "Shared with named recipients"

    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="annotations")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="annotations")
    page = models.PositiveIntegerField(default=1)
    text = models.TextField()
    visibility = models.CharField(max_length=12, choices=Visibility.choices, default=Visibility.PRIVATE)
    shared_with = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="shared_annotations"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("page", "created_at")

    def __str__(self):
        return f"{self.author} on {self.document} p{self.page}"
