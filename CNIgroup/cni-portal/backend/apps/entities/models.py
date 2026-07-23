"""
Group & entity structure (FR-ENT-1, DM-1).

Entities form a self-referential tree: holding company -> subsidiaries ->
sub-subsidiaries. Each entity owns its own boards, committees, documents,
role-assignments and registers. The multi-entity model exists from day one
(principle P3); with D-B1 the group tree is exposed in the UI from launch.
"""
from django.core.exceptions import ValidationError
from django.db import models

REQUIRED_STATUTORY_FIELDS = (
    "legal_name",
    "cac_rc_number",
    "incorporation_date",
    "registered_address",
    "financial_year_end",
)


class Entity(models.Model):
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="children",
    )
    legal_name = models.CharField(max_length=255)
    code = models.CharField(max_length=8, blank=True, default="", help_text="Short code for numbering, e.g. CNI")
    cac_rc_number = models.CharField("CAC RC number", max_length=32, blank=True, default="")
    incorporation_date = models.DateField(null=True, blank=True)
    registered_address = models.TextField(blank=True, default="")
    share_capital = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    financial_year_end = models.CharField(max_length=5, blank=True, default="", help_text="MM-DD")
    company_secretary = models.CharField(max_length=255, blank=True, default="")
    auditors = models.CharField(max_length=255, blank=True, default="")
    regulators = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "entities"
        ordering = ("legal_name",)

    def __str__(self):
        return self.legal_name

    def _assert_no_cycle(self):
        node = self.parent
        while node is not None:
            if self.pk is not None and node.pk == self.pk:
                raise ValidationError("An entity cannot be its own ancestor.")
            node = node.parent

    def clean(self):
        self._assert_no_cycle()

    def save(self, *args, **kwargs):
        self._assert_no_cycle()
        super().save(*args, **kwargs)

    @property
    def is_complete(self):
        """True iff all CAMA-required statutory particulars are present (FR-ENT-1)."""
        return all(bool(getattr(self, f)) for f in REQUIRED_STATUTORY_FIELDS)

    def ancestors(self):
        node, seen = self.parent, []
        while node is not None:
            seen.append(node)
            node = node.parent
        return seen

    def descendants(self):
        """All entities below this one in the tree (breadth-first)."""
        result, stack = [], list(self.children.all())
        while stack:
            node = stack.pop()
            result.append(node)
            stack.extend(node.children.all())
        return result


class EntitySettings(models.Model):
    """Per-entity configuration (FR-ADM-1): branding, numbering, retention, policy."""

    entity = models.OneToOneField(Entity, on_delete=models.CASCADE, related_name="settings")
    brand_primary_color = models.CharField(max_length=9, default="#2563EB")
    logo_url = models.CharField(max_length=512, blank=True, default="")
    resolution_number_format = models.CharField(max_length=64, default="{code}/{body}/{year}/{seq}")
    retention_days = models.PositiveIntegerField(default=0, help_text="0 = retain indefinitely")
    notification_policy = models.JSONField(default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "entity settings"

    def __str__(self):
        return f"Settings — {self.entity.legal_name}"
