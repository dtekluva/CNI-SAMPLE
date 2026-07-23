"""
Access control API (FR-RBAC-1) — surfaces role assignments so the Company
Secretary can see and manage who can do what, per entity.

Reads are scoped: a group admin sees every assignment within their visible
entities (plus group-level roles); everyone else sees only their own. Writes
(assign / revoke) are group-admin only and audited via the rbac services.
"""
from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from apps.accounts.permissions import IsMFAVerified
from apps.rbac.resolution import entities_for_user, is_group_admin

from .models import Role, RoleAssignment
from .services import assign_role, revoke_role

User = get_user_model()


class RoleAssignmentSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source="user.email", read_only=True)
    user_name = serializers.CharField(source="user.name", read_only=True)
    role_display = serializers.CharField(source="get_role_display", read_only=True)
    scope = serializers.SerializerMethodField()

    class Meta:
        model = RoleAssignment
        fields = ["id", "user", "user_email", "user_name", "role", "role_display", "entity", "scope", "created_at"]
        read_only_fields = ["id", "created_at"]

    def get_scope(self, obj):
        return obj.entity.legal_name if obj.entity_id else "Group (all entities)"


class RoleAssignmentViewSet(viewsets.ModelViewSet):
    serializer_class = RoleAssignmentSerializer
    permission_classes = [IsMFAVerified]

    def get_queryset(self):
        qs = RoleAssignment.objects.select_related("user", "entity")
        if is_group_admin(self.request.user):
            scope = entities_for_user(self.request.user)
            return qs.filter(Q(entity__in=scope) | Q(entity__isnull=True))
        return qs.filter(user=self.request.user)

    def _require_admin(self):
        if not is_group_admin(self.request.user):
            raise PermissionDenied("Only a group Company Secretary or Super Administrator can manage roles.")

    def create(self, request, *args, **kwargs):
        self._require_admin()
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        assignment = assign_role(
            actor=request.user,
            user=ser.validated_data["user"],
            role=ser.validated_data["role"],
            entity=ser.validated_data.get("entity"),
        )
        return Response(self.get_serializer(assignment).data, status=201)

    def destroy(self, request, *args, **kwargs):
        self._require_admin()
        revoke_role(actor=request.user, assignment=self.get_object())
        return Response(status=204)

    @action(detail=False, methods=["get"])
    def options(self, request):
        """Assignable roles / users / entities — group admins only (empty otherwise)."""
        if not is_group_admin(request.user):
            return Response({"can_manage": False, "roles": [], "users": [], "entities": []})
        return Response({
            "can_manage": True,
            "roles": [{"value": r.value, "label": r.label} for r in Role],
            "users": [
                {"id": u.id, "email": u.email, "name": u.name}
                for u in User.objects.filter(is_active=True).order_by("name", "email")
            ],
            "entities": [
                {"id": e.id, "legal_name": e.legal_name}
                for e in entities_for_user(request.user).order_by("legal_name")
            ],
        })
