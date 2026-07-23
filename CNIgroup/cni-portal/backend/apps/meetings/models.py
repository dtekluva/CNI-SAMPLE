"""
Meetings lifecycle (FR-MTG-1). Entity-scoped meetings with recurring series and
per-invitee timezone rendering (diaspora directors). Notice, agenda, attendance
and quorum are layered on in T-C2..C4.
"""
from zoneinfo import ZoneInfo

from django.conf import settings
from django.db import models


class Meeting(models.Model):
    class Type(models.TextChoices):
        BOARD = "board", "Board"
        COMMITTEE = "committee", "Committee"
        AGM = "agm", "AGM"
        EGM = "egm", "EGM"

    entity = models.ForeignKey(
        "entities.Entity", on_delete=models.CASCADE, related_name="meetings"
    )
    title = models.CharField(max_length=255)
    meeting_type = models.CharField(max_length=16, choices=Type.choices, default=Type.BOARD)
    starts_at = models.DateTimeField()
    timezone = models.CharField(max_length=64, default="Africa/Lagos")
    location = models.CharField(max_length=255, blank=True, default="")
    is_virtual = models.BooleanField(default=False)
    virtual_link = models.URLField(blank=True, default="")
    virtual_provider = models.CharField(max_length=32, blank=True, default="", help_text="Zoom / Teams / Meet")
    dial_in = models.CharField(max_length=128, blank=True, default="", help_text="Phone dial-in fallback")
    recording_url = models.URLField(blank=True, default="", help_text="Stored recording (retention applies)")
    quorum = models.PositiveIntegerField(default=0, help_text="Minimum present for a valid meeting")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("starts_at",)

    def __str__(self):
        return f"{self.title} ({self.starts_at:%Y-%m-%d})"

    def start_in_tz(self, tz_name):
        """Render the start instant in a given invitee's timezone."""
        return self.starts_at.astimezone(ZoneInfo(tz_name))


class ConsentToShortNotice(models.Model):
    """A member's recorded consent to hold a meeting inside the statutory notice
    period (FR-MTG-2, CAMA)."""

    meeting = models.ForeignKey(
        Meeting, on_delete=models.CASCADE, related_name="short_notice_consents"
    )
    member = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    consented_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("meeting", "member")


class AgendaItem(models.Model):
    """An item on a meeting agenda (FR-MTG-3). Position drives ordering and the
    auto-numbered table of contents."""

    class ItemType(models.TextChoices):
        APPROVAL = "approval", "For Approval"
        DISCUSSION = "discussion", "For Discussion"
        NOTING = "noting", "For Noting"

    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name="agenda_items")
    title = models.CharField(max_length=255)
    item_type = models.CharField(max_length=16, choices=ItemType.choices, default=ItemType.DISCUSSION)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="owned_agenda_items",
    )
    time_allocation_minutes = models.PositiveIntegerField(default=0)
    position = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("position", "id")

    def __str__(self):
        return self.title


class Attendance(models.Model):
    """Per-member attendance for a meeting (FR-MTG-5): mode, status, proxy."""

    class Mode(models.TextChoices):
        PHYSICAL = "physical", "Physical"
        VIRTUAL = "virtual", "Virtual"
        PROXY = "proxy", "Proxy"

    class Status(models.TextChoices):
        PRESENT = "present", "Present"
        APOLOGY = "apology", "Apology"
        ABSENT = "absent", "Absent"

    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name="attendances")
    member = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="attendances")
    mode = models.CharField(max_length=16, choices=Mode.choices, default=Mode.PHYSICAL)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PRESENT)
    proxy_for = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="proxies_held",
    )
    recorded_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("meeting", "member")


class MeetingSession(models.Model):
    """
    In-meeting mode (FR-MTG-7): the live state of a running meeting — which
    agenda item is on the floor and when it took the floor. Attendees in
    'follow' mode read current_item to stay on the presenter's page; the live
    tracker compares elapsed against the item's time allocation.
    """
    meeting = models.OneToOneField(Meeting, on_delete=models.CASCADE, related_name="session")
    active = models.BooleanField(default=False)
    current_item = models.ForeignKey(
        AgendaItem, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    item_started_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Session — {self.meeting.title} ({'live' if self.active else 'idle'})"
