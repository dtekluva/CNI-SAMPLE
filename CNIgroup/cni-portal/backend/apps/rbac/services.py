from apps.audit.models import AuditEvent

from .models import RoleAssignment


def assign_role(*, actor, user, role, entity=None):
    """Grant a scoped role and audit it (FR-RBAC-1)."""
    assignment, created = RoleAssignment.objects.get_or_create(
        user=user, role=role, entity=entity
    )
    AuditEvent.objects.record(
        action="role.assigned",
        actor=actor,
        target=assignment,
        metadata={
            "user": user.pk,
            "role": role,
            "entity": entity.pk if entity else None,
            "created": created,
        },
    )
    return assignment


def revoke_role(*, actor, assignment):
    """Revoke a role assignment and audit it (target the user; assignment is deleted)."""
    AuditEvent.objects.record(
        action="role.revoked",
        actor=actor,
        target=assignment.user,
        metadata={
            "user": assignment.user_id,
            "role": assignment.role,
            "entity": assignment.entity_id,
        },
    )
    assignment.delete()
