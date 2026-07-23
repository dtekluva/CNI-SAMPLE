"""
User lifecycle (FR-ADM-2, principle P6 — the record survives the person).

Offboarding revokes access (deactivate + drop role assignments) but keeps the
user row and all audit attribution intact, so a departed director's historical
actions remain correctly attributed.
"""
from django.contrib.auth import get_user_model

from apps.audit.models import AuditEvent


def onboard_user(*, actor, email, name="", roles=None):
    """Create (or fetch) a user, optionally assign scoped roles, and audit it."""
    User = get_user_model()
    user, created = User.objects.get_or_create(email=email, defaults={"name": name})
    AuditEvent.objects.record(
        action="user.onboarded", actor=actor, target=user,
        metadata={"email": email, "created": created},
    )
    if roles:
        from apps.rbac.services import assign_role

        for role, entity in roles:
            assign_role(actor=actor, user=user, role=role, entity=entity)
    return user


def offboard_user(*, actor, user):
    """Revoke access but preserve history + attribution (P6)."""
    from apps.rbac.models import RoleAssignment

    user.is_active = False
    user.save(update_fields=["is_active"])
    RoleAssignment.objects.filter(user=user).delete()
    AuditEvent.objects.record(action="user.offboarded", actor=actor, target=user)


def bulk_import_users(*, actor, rows):
    """rows: iterable of {'email': ..., 'name': ...}."""
    return [onboard_user(actor=actor, email=r["email"], name=r.get("name", "")) for r in rows]
