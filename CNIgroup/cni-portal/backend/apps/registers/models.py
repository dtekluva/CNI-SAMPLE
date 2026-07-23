"""
Statutory registers per entity (FR-ENT-3, DM — CAMA 2020).

CAMA requires companies to keep statutory registers (members s.109, directors
s.291, secretaries, charges s.226, persons with significant control s.119,
debenture holders). These are a *system of record*: an entry is never physically
deleted — when a party leaves the register it is **ceased** (an end-date is set)
so the historical position is provable to the CAC and auditors at any past date.

The register is deliberately schema-light: each register type carries different
particulars (shareholdings, appointment dates, charge amounts), so structured
`particulars` are held as JSON while the common statutory columns — who, from
when, until when — are first-class fields for filtering and export.
"""
from django.db import models


class RegisterType(models.TextChoices):
    MEMBERS = "members", "Register of Members"
    DIRECTORS = "directors", "Register of Directors"
    SECRETARIES = "secretaries", "Register of Secretaries"
    CHARGES = "charges", "Register of Charges"
    BENEFICIAL_OWNERS = "beneficial_owners", "Register of Persons with Significant Control"
    DEBENTURE_HOLDERS = "debenture_holders", "Register of Debenture Holders"


class RegisterEntry(models.Model):
    entity = models.ForeignKey(
        "entities.Entity", on_delete=models.PROTECT, related_name="register_entries"
    )
    register_type = models.CharField(max_length=32, choices=RegisterType.choices)
    party_name = models.CharField(max_length=255)
    particulars = models.JSONField(
        default=dict, blank=True, help_text="Register-specific fields (shares, address, charge amount…)"
    )
    effective_from = models.DateField(help_text="Date the party entered the register")
    ceased_on = models.DateField(
        null=True, blank=True, help_text="Date the party left; null = currently on the register"
    )
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "register entries"
        ordering = ("register_type", "party_name", "-effective_from")
        indexes = [models.Index(fields=["entity", "register_type", "ceased_on"])]

    def __str__(self):
        return f"{self.get_register_type_display()} — {self.party_name}"

    @property
    def is_active(self):
        """Currently on the register (has not been ceased)."""
        return self.ceased_on is None
