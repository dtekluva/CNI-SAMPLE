"""
Directors' interests & conflicts (FR-CONF-1/2 — CAMA ss.303–306).

An InterestDeclaration is a director's standing disclosure — a directorship,
shareholding or contractual interest held elsewhere — kept per entity so each
board sees the interests relevant to it. Like the statutory registers, a
declaration is withdrawn (end-dated), never deleted.

A ConflictDeclaration is the per-meeting act: "on this item, I am conflicted."
It optionally cites a standing interest and is what recusal enforcement
(FR-RBAC-2 / FR-VOTE-2) hangs off.
"""
from django.conf import settings
from django.db import models


class InterestDeclaration(models.Model):
    class Kind(models.TextChoices):
        DIRECTORSHIP = "directorship", "Directorship elsewhere"
        SHAREHOLDING = "shareholding", "Shareholding"
        CONTRACT = "contract", "Interest in a contract"
        OTHER = "other", "Other"

    entity = models.ForeignKey("entities.Entity", on_delete=models.PROTECT, related_name="interest_declarations")
    director = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="interest_declarations")
    kind = models.CharField(max_length=16, choices=Kind.choices)
    party = models.CharField(max_length=255, help_text="The company/counterparty the interest is in")
    details = models.TextField(blank=True, default="")
    declared_on = models.DateField()
    withdrawn_on = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-declared_on", "party")

    def __str__(self):
        return f"{self.director} — {self.get_kind_display()}: {self.party}"

    @property
    def is_active(self):
        return self.withdrawn_on is None


class ConflictDeclaration(models.Model):
    meeting = models.ForeignKey("meetings.Meeting", on_delete=models.CASCADE, related_name="conflict_declarations")
    agenda_item = models.ForeignKey(
        "meetings.AgendaItem", null=True, blank=True, on_delete=models.CASCADE, related_name="conflict_declarations"
    )
    director = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="conflict_declarations")
    interest = models.ForeignKey(
        InterestDeclaration, null=True, blank=True, on_delete=models.SET_NULL, related_name="conflicts"
    )
    note = models.TextField(blank=True, default="")
    declared_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("meeting", "agenda_item", "director")
        ordering = ("-declared_at",)

    def __str__(self):
        scope = self.agenda_item.title if self.agenda_item_id else "whole meeting"
        return f"{self.director} conflicted on {scope}"
