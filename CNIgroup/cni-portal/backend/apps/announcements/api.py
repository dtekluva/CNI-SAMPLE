"""
Announcements API (FR-NOT-2) — scoped; leadership posts and sees receipts,
directors read (which records a receipt). Audited.
"""
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from apps.accounts.permissions import IsMFAVerified
from apps.audit.models import AuditEvent
from apps.rbac.models import Role
from apps.rbac.permissions import CanAccessContent
from apps.rbac.resolution import entities_for_user, has_entity_access, has_role, is_group_admin

from .models import Announcement, ReadReceipt


def _can_post(user, entity):
    return is_group_admin(user) or has_role(user, entity, Role.CHAIRMAN, Role.COMPANY_SECRETARY)


class AnnouncementSerializer(serializers.ModelSerializer):
    posted_by_name = serializers.SerializerMethodField()
    read_by_me = serializers.SerializerMethodField()
    read_count = serializers.IntegerField(source="receipts.count", read_only=True)

    class Meta:
        model = Announcement
        fields = ["id", "entity", "title", "body", "posted_by", "posted_by_name",
                  "posted_at", "read_by_me", "read_count"]
        read_only_fields = ["id", "posted_by", "posted_at"]

    def get_posted_by_name(self, obj):
        return (obj.posted_by.name or obj.posted_by.email) if obj.posted_by_id else None

    def get_read_by_me(self, obj):
        u = self.context["request"].user
        return obj.receipts.filter(user=u).exists()


class AnnouncementViewSet(viewsets.ModelViewSet):
    serializer_class = AnnouncementSerializer
    permission_classes = [IsMFAVerified, CanAccessContent]

    def get_queryset(self):
        return Announcement.objects.filter(entity__in=entities_for_user(self.request.user)).prefetch_related("receipts")

    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        entity = ser.validated_data["entity"]
        if not _can_post(request.user, entity):
            raise PermissionDenied("Only the Chairman or Company Secretary may post announcements.")
        ann = ser.save(posted_by=request.user)
        AuditEvent.objects.record(action="announcement.posted", actor=request.user, target=ann)
        return Response(self.get_serializer(ann).data, status=201)

    @action(detail=True, methods=["post"])
    def read(self, request, pk=None):
        """Opening an announcement records a read receipt (FR-NOT-2)."""
        ann = self.get_object()
        _, created = ReadReceipt.objects.get_or_create(announcement=ann, user=request.user)
        if created:
            AuditEvent.objects.record(action="announcement.read", actor=request.user, target=ann)
        return Response({"read": True})

    @action(detail=True, methods=["get"])
    def receipts(self, request, pk=None):
        """Who has read it — leadership only."""
        ann = self.get_object()
        if not _can_post(request.user, ann.entity):
            raise PermissionDenied("Only leadership may view read receipts.")
        return Response([
            {"user": r.user_id, "name": r.user.name or r.user.email, "read_at": r.read_at}
            for r in ann.receipts.select_related("user")
        ])
