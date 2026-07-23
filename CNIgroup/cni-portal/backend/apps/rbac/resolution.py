"""
Permission resolution (FR-RBAC-1, PRD P2 — least privilege, default-deny).

Resolves the set of entities a user may act within:
- a group-level role (entity is null) -> the whole group;
- an entity-scoped role -> that entity AND its descendants (a holdco role
  cascades to subsidiaries);
- no roles -> nothing (default-deny).
Every list/detail path filters through here so nothing is globally readable.
"""
from django.db.models import Q
from django.utils import timezone

from apps.entities.models import Entity


def entities_for_user(user):
    if not (user and getattr(user, "is_authenticated", False)):
        return Entity.objects.none()
    assignments = list(user.role_assignments.all())
    if any(a.entity_id is None for a in assignments):
        return Entity.objects.all()
    ids = set()
    for a in assignments:
        if a.entity_id:
            ids.add(a.entity_id)
            ids.update(e.pk for e in a.entity.descendants())
    return Entity.objects.filter(pk__in=ids)


def has_entity_access(user, entity):
    return entities_for_user(user).filter(pk=entity.pk).exists()


def roles_on_entity(user, entity):
    from apps.rbac.models import RoleAssignment

    return set(
        RoleAssignment.objects.for_user_entity(user, entity).values_list("role", flat=True)
    )


def has_role(user, entity, *roles):
    return bool(roles_on_entity(user, entity) & set(roles))


def has_active_break_glass(user, entity):
    from apps.rbac.models import BreakGlassGrant

    now = timezone.now()
    return (
        BreakGlassGrant.objects.filter(user=user, expires_at__gt=now)
        .filter(Q(entity=entity) | Q(entity__isnull=True))
        .exists()
    )


def can_access_content(user, entity):
    """Content access = a resolving role OR an active break-glass grant (FR-RBAC-3)."""
    return has_entity_access(user, entity) or has_active_break_glass(user, entity)


def is_group_admin(user):
    """Group-level Company Secretary or Super Administrator (may create entities)."""
    from apps.rbac.models import Role, RoleAssignment

    return RoleAssignment.objects.filter(
        user=user,
        entity__isnull=True,
        role__in=[Role.SUPER_ADMIN, Role.COMPANY_SECRETARY],
    ).exists()
