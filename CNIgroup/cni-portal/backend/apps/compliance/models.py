"""
Compliance & statutory calendar (FR-CMP-1/2 — CAMA, CBN, FIRS, NDPA).

Each entity carries its recurring statutory obligations (annual returns,
licence renewals, tax filings, data-protection audits). An obligation has a
next-due date and a RAG status derived from it; recording a filing captures
the evidence and rolls the due date forward by the obligation's frequency —
the calendar maintains itself.
"""
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class ComplianceObligation(models.Model):
    class Frequency(models.TextChoices):
        ANNUAL = "annual", "Annual"
        QUARTERLY = "quarterly", "Quarterly"
        MONTHLY = "monthly", "Monthly"
        ONCE = "once", "One-off"

    entity = models.ForeignKey("entities.Entity", on_delete=models.CASCADE, related_name="obligations")
    title = models.CharField(max_length=255)
    regulator = models.CharField(max_length=64, help_text="CAC, CBN, FIRS, NDPC…")
    frequency = models.CharField(max_length=12, choices=Frequency.choices, default=Frequency.ANNUAL)
    due_date = models.DateField(help_text="Next due date; rolls forward on filing")
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("due_date",)

    def __str__(self):
        return f"{self.title} ({self.regulator}) — {self.entity.legal_name}"

    @property
    def rag(self):
        """red = overdue · amber = due within 30 days · green = on track."""
        today = timezone.now().date()
        if self.due_date < today:
            return "red"
        if (self.due_date - today).days <= 30:
            return "amber"
        return "green"

    def roll_forward(self):
        step = {
            self.Frequency.ANNUAL: timedelta(days=365),
            self.Frequency.QUARTERLY: timedelta(days=91),
            self.Frequency.MONTHLY: timedelta(days=30),
        }.get(self.Frequency(self.frequency))
        if step:
            self.due_date = self.due_date + step
            self.save(update_fields=["due_date"])


class Filing(models.Model):
    obligation = models.ForeignKey(ComplianceObligation, on_delete=models.CASCADE, related_name="filings")
    period_label = models.CharField(max_length=64, help_text="e.g. FY2025, Q2 2026")
    filed_on = models.DateField()
    evidence = models.CharField(max_length=512, blank=True, default="",
                                help_text="Receipt no., acknowledgement ref., or document link")
    filed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-filed_on",)

    def __str__(self):
        return f"{self.obligation.title} — {self.period_label}"
