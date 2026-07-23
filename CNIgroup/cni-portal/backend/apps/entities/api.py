from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied

from apps.accounts.permissions import IsMFAVerified
from apps.audit.models import AuditEvent
from apps.rbac.permissions import CanAccessContent
from apps.rbac.resolution import entities_for_user, is_group_admin

from .models import Entity
from .serializers import EntitySerializer


class EntityViewSet(viewsets.ModelViewSet):
    """
    Entity CRUD, permission-scoped (FR-ENT-1). List returns only the entities
    the caller can access; create is group-admin only; all mutations are audited.
    """

    serializer_class = EntitySerializer
    permission_classes = [IsMFAVerified, CanAccessContent]

    def get_queryset(self):
        return entities_for_user(self.request.user)

    def create(self, request, *args, **kwargs):
        if not is_group_admin(request.user):
            raise PermissionDenied(
                "Only a group Company Secretary or Super Administrator can create entities."
            )
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        entity = serializer.save()
        AuditEvent.objects.record(action="entity.created", actor=self.request.user, target=entity)

    def perform_update(self, serializer):
        entity = serializer.save()
        AuditEvent.objects.record(action="entity.updated", actor=self.request.user, target=entity)

    def perform_destroy(self, instance):
        AuditEvent.objects.record(
            action="entity.deleted",
            actor=self.request.user,
            target=instance,
            metadata={"legal_name": instance.legal_name},
        )
        instance.delete()
