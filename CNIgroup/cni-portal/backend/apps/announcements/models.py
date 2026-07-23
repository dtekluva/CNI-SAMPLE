"""
Announcements with read receipts (FR-NOT-2).

The Chairman/Cosec posts a board circular to an entity; each director's opening
of it is recorded as a receipt, so leadership can see who has and hasn't read it.
"""
from django.conf import settings
from django.db import models


class Announcement(models.Model):
    entity = models.ForeignKey("entities.Entity", on_delete=models.CASCADE, related_name="announcements")
    title = models.CharField(max_length=255)
    body = models.TextField()
    posted_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    posted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-posted_at",)

    def __str__(self):
        return self.title


class ReadReceipt(models.Model):
    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE, related_name="receipts")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="read_receipts")
    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("announcement", "user")
