"""
Role-based access control (FR-RBAC-1, PRD §3).

One identity carries many scoped RoleAssignments. A role is scoped to an entity,
or group-level (entity is null) so a group chairman/cosec can act across the
group (D-B1). Committee/meeting scoping is layered on in later tasks.
Permission *resolution* (who can do what) is T-B3; this task is the model + audit.
"""
from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone


class Role(models.TextChoices):
    SUPER_ADMIN = "super_admin", "Super Administrator"
    COMPANY_SECRETARY = "company_secretary", "Company Secretary"
    CHAIRMAN = "chairman", "Chairman"
    EXECUTIVE_DIRECTOR = "executive_director", "Executive Director"
    NON_EXECUTIVE_DIRECTOR = "non_executive_director", "Non-Executive Director"
    INDEPENDENT_DIRECTOR = "independent_director", "Independent Director"
    COMMITTEE_MEMBER = "committee_member", "Committee Member"
    PRESENTER = "presenter", "Presenter/Invitee"
    AUDITOR = "auditor", "Auditor"
    LEGAL_COUNSEL = "legal_counsel", "Legal Counsel"
    PORTAL_ADMIN = "portal_admin", "Portal Administrator"


class RoleAssignmentManager(models.Manager):
    def for_user_entity(self, user, entity):
        """Assignments that apply to `entity` for `user` (entity-scoped OR group-level)."""
        return self.filter(user=user).filter(Q(entity=entity) | Q(entity__isnull=True))


class RoleAssignment(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="role_assignments"
    )
    role = models.CharField(max_length=32, choices=Role.choices)
    entity = models.ForeignKey(
        "entities.Entity",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="role_assignments",
        help_text="Null = group-level role",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    objects = RoleAssignmentManager()

    class Meta:
        unique_together = ("user", "role", "entity")

    @property
    def is_group_level(self):
        return self.entity_id is None

    def __str__(self):
        scope = self.entity.legal_name if self.entity_id else "GROUP"
        return f"{self.user} · {self.get_role_display()} @ {scope}"


class BreakGlassGrant(models.Model):
    """
    Time-boxed emergency content access for admins (FR-RBAC-3, NFR-SEC-4).
    Invoked with a stated reason; emits a high-severity audit event and notifies
    the Company Secretary. Admins have NO content access without one.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="break_glass_grants"
    )
    entity = models.ForeignKey(
        "entities.Entity", null=True, blank=True, on_delete=models.CASCADE
    )
    reason = models.TextField()
    granted_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        ordering = ("-granted_at",)

    def is_active(self, now=None):
        return self.expires_at > (now or timezone.now())

    def __str__(self):
        scope = self.entity.legal_name if self.entity_id else "GROUP"
        return f"break-glass {self.user} @ {scope} until {self.expires_at:%Y-%m-%d %H:%M}"
