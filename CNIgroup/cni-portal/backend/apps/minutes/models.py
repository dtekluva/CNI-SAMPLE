"""
Minutes (FR-MIN-1). Minutes are drafted item-by-item against the agenda, with
attendees auto-populated. Inline decisions (action/resolution) are captured per
block and promoted to formal Action/Resolution records in later tasks.
The draft -> adopt -> sign workflow is T-E2.
"""
from django.conf import settings
from django.db import models


class Minutes(models.Model):
    class State(models.TextChoices):
        DRAFT = "draft", "Draft"
        CHAIRMAN_REVIEW = "chairman_review", "Chairman review"
        CIRCULATED = "circulated", "Circulated for comment"
        ADOPTED = "adopted", "Adopted"
        SIGNED = "signed", "Signed"

    meeting = models.OneToOneField("meetings.Meeting", on_delete=models.CASCADE, related_name="minutes")
    state = models.CharField(max_length=20, choices=State.choices, default=State.DRAFT)
    attendees = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name="minutes_present")
    # Sealing (FR-MIN-3): stamped when the minutes are signed — the record becomes
    # immutable and tamper-evident. A later correction is a fresh minute, not an edit.
    content_hash = models.CharField(max_length=64, blank=True, default="")
    signed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="minutes_signed"
    )
    signed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "minutes"

    def __str__(self):
        return f"Minutes — {self.meeting.title}"

    @property
    def entity(self):
        """Content scoping resolves through the meeting (used by CanAccessContent)."""
        return self.meeting.entity


class MinuteBlock(models.Model):
    minutes = models.ForeignKey(Minutes, on_delete=models.CASCADE, related_name="blocks")
    agenda_item = models.ForeignKey("meetings.AgendaItem", on_delete=models.CASCADE, related_name="minute_blocks")
    text = models.TextField(blank=True, default="")

    class Meta:
        unique_together = ("minutes", "agenda_item")
        ordering = ("agenda_item__position",)


class InlineDecision(models.Model):
    """An action/resolution captured inline while minuting (FR-MIN-1)."""

    class Kind(models.TextChoices):
        ACTION = "action", "Action"
        RESOLUTION = "resolution", "Resolution"

    block = models.ForeignKey(MinuteBlock, on_delete=models.CASCADE, related_name="inline_decisions")
    kind = models.CharField(max_length=16, choices=Kind.choices)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class MinuteComment(models.Model):
    """A director's comment on draft minutes; must be dispositioned before adoption
    (FR-MIN-2)."""

    minutes = models.ForeignKey(Minutes, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    text = models.TextField()
    dispositioned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
