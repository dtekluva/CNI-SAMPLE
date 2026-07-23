"""
Minute book API (FR-MIN-3) — the per-entity statutory record of signed minutes,
compiled chronologically, exportable as an immutable PDF, and tamper-verifiable.
"""
from django.http import HttpResponse
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.permissions import IsMFAVerified
from apps.audit.models import AuditEvent
from apps.rbac.permissions import CanAccessContent
from apps.rbac.resolution import entities_for_user

from .models import Minutes
from .pdf import render_minutes_pdf
from .services import compute_minutes_hash


class MinuteBookSerializer(serializers.ModelSerializer):
    meeting_title = serializers.CharField(source="meeting.title", read_only=True)
    meeting_date = serializers.DateTimeField(source="meeting.starts_at", read_only=True)
    entity = serializers.IntegerField(source="meeting.entity_id", read_only=True)
    entity_name = serializers.CharField(source="meeting.entity.legal_name", read_only=True)
    signed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Minutes
        fields = ["id", "state", "content_hash", "signed_at", "signed_by_name",
                  "meeting_title", "meeting_date", "entity", "entity_name"]

    def get_signed_by_name(self, obj):
        return (obj.signed_by.name or obj.signed_by.email) if obj.signed_by_id else None


class MinuteBookViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = MinuteBookSerializer
    permission_classes = [IsMFAVerified, CanAccessContent]

    def get_queryset(self):
        qs = (
            Minutes.objects.filter(
                meeting__entity__in=entities_for_user(self.request.user),
                state=Minutes.State.SIGNED,
            )
            .select_related("meeting", "meeting__entity", "signed_by")
            .order_by("meeting__starts_at")
        )
        entity = self.request.query_params.get("entity")
        if entity:
            qs = qs.filter(meeting__entity_id=entity)
        return qs

    @action(detail=True, methods=["get"])
    def pdf(self, request, pk=None):
        m = self.get_object()
        AuditEvent.objects.record(action="minutebook.exported", actor=request.user, target=m)
        pdf = render_minutes_pdf(minutes=m, watermark=f"Prepared for {request.user.email}")
        resp = HttpResponse(pdf, content_type="application/pdf")
        resp["Content-Disposition"] = f'inline; filename="minutes-{m.meeting_id}.pdf"'
        return resp

    @action(detail=True, methods=["get"])
    def verify(self, request, pk=None):
        """Recompute the hash and compare to the seal — proves the record is intact."""
        m = self.get_object()
        current = compute_minutes_hash(m)
        intact = bool(m.content_hash) and current == m.content_hash
        return Response({"stored": m.content_hash, "current": current, "intact": intact})
