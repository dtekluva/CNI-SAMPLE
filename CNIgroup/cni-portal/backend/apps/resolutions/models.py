"""
Resolutions (FR-RES-1). Board resolutions with mover/seconder, votes and outcome,
auto-numbered per entity (‹CODE›/BD/‹YEAR›/‹SEQ›, cosec-confirmable — D-B6).
Circular resolutions and CTC generation are T-F2 / T-F3.
"""
from django.conf import settings
from django.db import models


class Resolution(models.Model):
    class Kind(models.TextChoices):
        BOARD = "board", "Board"
        CIRCULAR = "circular", "Circular"

    class VotingMode(models.TextChoices):
        OPEN = "open", "Open (show of hands)"
        SECRET = "secret", "Secret ballot"
        POLL = "poll", "Poll (weighted)"

    class ResolutionClass(models.TextChoices):
        ORDINARY = "ordinary", "Ordinary (simple majority)"
        SPECIAL = "special", "Special (≥75%)"

    class Outcome(models.TextChoices):
        PENDING = "pending", "Pending"
        PASSED = "passed", "Passed"
        FAILED = "failed", "Failed"
        LAPSED = "lapsed", "Lapsed"

    entity = models.ForeignKey("entities.Entity", on_delete=models.CASCADE, related_name="resolutions")
    meeting = models.ForeignKey(
        "meetings.Meeting", null=True, blank=True, on_delete=models.SET_NULL, related_name="resolutions"
    )
    agenda_item = models.ForeignKey(
        "meetings.AgendaItem", null=True, blank=True, on_delete=models.SET_NULL, related_name="resolutions",
        help_text="The item this motion belongs to — used for item-level recusal in voting",
    )
    number = models.CharField(max_length=64)
    year = models.IntegerField()
    title = models.CharField(max_length=255)
    text = models.TextField()
    kind = models.CharField(max_length=16, choices=Kind.choices, default=Kind.BOARD)
    voting_mode = models.CharField(max_length=16, choices=VotingMode.choices, default=VotingMode.OPEN)
    resolution_class = models.CharField(
        max_length=16, choices=ResolutionClass.choices, default=ResolutionClass.ORDINARY,
        help_text="Special resolutions require the statutory 75% threshold (CAMA)",
    )
    amount = models.DecimalField(
        max_digits=18, decimal_places=2, null=True, blank=True,
        help_text="Monetary value of the decision, validated against the DoA matrix",
    )
    category = models.CharField(max_length=64, blank=True, default="", help_text="DoA category, e.g. Capital expenditure")
    mover = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="moved_resolutions"
    )
    seconder = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="seconded_resolutions"
    )
    outcome = models.CharField(max_length=16, choices=Outcome.choices, default=Outcome.PENDING)
    effective_date = models.DateField(null=True, blank=True)
    threshold = models.PositiveIntegerField(default=0, help_text="Signatures required (circular)")
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("entity", "number")
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.number} — {self.title}"


class Signature(models.Model):
    """A director's e-signature on a (circular) resolution (FR-RES-2)."""

    resolution = models.ForeignKey(Resolution, on_delete=models.CASCADE, related_name="signatures")
    signer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    certificate = models.CharField(max_length=512)
    signed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("resolution", "signer")


class CertifiedTrueCopy(models.Model):
    """A Certified True Copy issued for banks/CAC (FR-RES-4)."""

    resolution = models.ForeignKey(Resolution, on_delete=models.CASCADE, related_name="ctcs")
    reference = models.CharField(max_length=80)
    body = models.TextField()
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    issued_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.reference


class Vote(models.Model):
    class Choice(models.TextChoices):
        FOR = "for", "For"
        AGAINST = "against", "Against"
        ABSTAIN = "abstain", "Abstain"
        RECUSED = "recused", "Recused"

    resolution = models.ForeignKey(Resolution, on_delete=models.CASCADE, related_name="votes")
    voter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    choice = models.CharField(max_length=16, choices=Choice.choices)
    weight = models.PositiveIntegerField(default=1, help_text="Voting weight for poll mode (e.g. shares)")
    cast_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("resolution", "voter")


class DelegationRule(models.Model):
    """
    A row in the Delegation of Authority matrix (FR-RES-5): for a category of
    decision, an approver body may authorize up to a monetary limit. Tiers order
    the escalation — the lowest tier whose limit covers an amount is the required
    approver; an amount above every tier exceeds delegated authority.
    """
    entity = models.ForeignKey("entities.Entity", on_delete=models.CASCADE, related_name="delegation_rules")
    category = models.CharField(max_length=64, help_text="e.g. Capital expenditure, Disposals, Contracts")
    approver = models.CharField(max_length=128, help_text="e.g. Managing Director, Board Risk Committee, Full Board")
    max_amount = models.DecimalField(max_digits=18, decimal_places=2, help_text="Authority limit (NGN)")
    tier = models.PositiveIntegerField(default=1, help_text="Escalation order; higher = more authority")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("entity__legal_name", "category", "tier")
        unique_together = ("entity", "category", "tier")

    def __str__(self):
        return f"{self.category}: {self.approver} ≤ {self.max_amount}"
