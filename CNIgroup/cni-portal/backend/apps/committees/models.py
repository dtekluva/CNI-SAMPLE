"""
Committees (FR-COM-1/2/3).

A committee belongs to an entity's board, carries a charter (its terms of
reference), has members with defined terms (rotation is a first-class fact,
not a spreadsheet), and reports up to the board — each report is a record that
the board formally notes.
"""
from django.conf import settings
from django.db import models
from django.utils import timezone


class Committee(models.Model):
    entity = models.ForeignKey("entities.Entity", on_delete=models.CASCADE, related_name="committees")
    name = models.CharField(max_length=255)
    charter = models.TextField(blank=True, default="", help_text="Terms of reference")
    charter_adopted_on = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("entity", "name")
        ordering = ("entity__legal_name", "name")

    def __str__(self):
        return f"{self.name} — {self.entity.legal_name}"


class CommitteeMembership(models.Model):
    class Role(models.TextChoices):
        CHAIR = "chair", "Chair"
        MEMBER = "member", "Member"

    committee = models.ForeignKey(Committee, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="committee_memberships")
    role = models.CharField(max_length=12, choices=Role.choices, default=Role.MEMBER)
    term_start = models.DateField()
    term_end = models.DateField(null=True, blank=True, help_text="Rotation date; null = open-ended")
    ended_on = models.DateField(null=True, blank=True, help_text="Actual end (resignation/rotation)")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-role", "term_start")

    def __str__(self):
        return f"{self.user} · {self.get_role_display()} of {self.committee.name}"

    @property
    def is_active(self):
        today = timezone.now().date()
        if self.ended_on and self.ended_on <= today:
            return False
        return self.term_start <= today

    @property
    def expires_soon(self):
        """Term ends within 90 days — rotation planning flag (FR-COM-2)."""
        if not self.term_end or not self.is_active:
            return False
        return (self.term_end - timezone.now().date()).days <= 90


class CommitteeReport(models.Model):
    class Status(models.TextChoices):
        SUBMITTED = "submitted", "Submitted to board"
        NOTED = "noted", "Noted by the board"

    committee = models.ForeignKey(Committee, on_delete=models.CASCADE, related_name="reports")
    meeting = models.ForeignKey(
        "meetings.Meeting", null=True, blank=True, on_delete=models.SET_NULL, related_name="committee_reports",
        help_text="The board meeting this report goes to",
    )
    title = models.CharField(max_length=255)
    summary = models.TextField()
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.SUBMITTED)
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    submitted_at = models.DateTimeField(auto_now_add=True)
    noted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-submitted_at",)

    def __str__(self):
        return f"{self.title} ({self.committee.name})"
