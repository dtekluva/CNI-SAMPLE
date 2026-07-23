"""
Action items (FR-ACT-1). Captured in-meeting with an owner (a portal user, or a
non-member such as management named in owner_name), a due date, and a link back
to the source agenda item. Reminders/escalation and dashboards are Phase 2.
"""
from django.conf import settings
from django.db import models


class Action(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        DONE = "done", "Done"

    entity = models.ForeignKey("entities.Entity", on_delete=models.CASCADE, related_name="actions")
    meeting = models.ForeignKey(
        "meetings.Meeting", null=True, blank=True, on_delete=models.SET_NULL, related_name="actions"
    )
    agenda_item = models.ForeignKey(
        "meetings.AgendaItem", null=True, blank=True, on_delete=models.SET_NULL, related_name="actions"
    )
    title = models.CharField(max_length=255)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="owned_actions"
    )
    owner_name = models.CharField(max_length=255, blank=True, default="", help_text="For non-member owners")
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=8, choices=Status.choices, default=Status.OPEN)
    evidence = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("due_date", "id")

    def __str__(self):
        return self.title
