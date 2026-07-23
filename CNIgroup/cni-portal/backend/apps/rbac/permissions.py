from rest_framework.permissions import BasePermission

from .resolution import can_access_content, has_entity_access


def _entity_of(obj):
    return obj if obj.__class__.__name__ == "Entity" else getattr(obj, "entity", None)


class HasEntityAccess(BasePermission):
    """
    Object-level entity scoping by ROLE only (PRD P2). Default-deny.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        entity = _entity_of(obj)
        return has_entity_access(request.user, entity) if entity is not None else False


class CanAccessContent(BasePermission):
    """
    Content access = a resolving role OR an active break-glass grant (NFR-SEC-4).
    Deliberately ignores is_staff/is_superuser: a platform admin has NO silent
    content access — admin != reader.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        entity = _entity_of(obj)
        return can_access_content(request.user, entity) if entity is not None else False
