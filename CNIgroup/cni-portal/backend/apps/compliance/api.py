"""
Compliance calendar API (FR-CMP-1/2) — scoped; the cosec maintains the
calendar, filings carry evidence and roll the due date forward. Audited.
"""
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import MethodNotAllowed, PermissionDenied
from rest_framework.response import Response

from apps.accounts.permissions import IsMFAVerified
from apps.audit.models import AuditEvent
from apps.rbac.permissions import CanAccessContent
from apps.rbac.resolution import entities_for_user, has_entity_access, is_group_admin

from .models import ComplianceObligation, Filing


class FilingSerializer(serializers.ModelSerializer):
    filed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Filing
        fields = ["id", "obligation", "period_label", "filed_on", "evidence", "filed_by", "filed_by_name", "created_at"]
        read_only_fields = ["id", "filed_by", "created_at"]

    def get_filed_by_name(self, obj):
        if not obj.filed_by_id:
            return None
        return obj.filed_by.name or obj.filed_by.email


class ObligationSerializer(serializers.ModelSerializer):
    entity_name = serializers.CharField(source="entity.legal_name", read_only=True)
    rag = serializers.CharField(read_only=True)
    last_filing = serializers.SerializerMethodField()

    class Meta:
        model = ComplianceObligation
        fields = ["id", "entity", "entity_name", "title", "regulator", "frequency",
                  "due_date", "description", "rag", "last_filing", "created_at"]
        read_only_fields = ["id", "created_at"]

    def get_last_filing(self, obj):
        f = obj.filings.first()
        return FilingSerializer(f).data if f else None


class ObligationViewSet(viewsets.ModelViewSet):
    serializer_class = ObligationSerializer
    permission_classes = [IsMFAVerified, CanAccessContent]

    def get_queryset(self):
        qs = ComplianceObligation.objects.filter(
            entity__in=entities_for_user(self.request.user)
        ).select_related("entity").prefetch_related("filings")
        entity = self.request.query_params.get("entity")
        if entity:
            qs = qs.filter(entity_id=entity)
        return qs

    def _admin_guard(self, entity):
        if not has_entity_access(self.request.user, entity):
            raise PermissionDenied("No access to that entity.")
        if not is_group_admin(self.request.user):
            raise PermissionDenied("Only the Company Secretary maintains the compliance calendar.")

    def perform_create(self, serializer):
        self._admin_guard(serializer.validated_data["entity"])
        obligation = serializer.save()
        AuditEvent.objects.record(action="compliance.obligation_created", actor=self.request.user, target=obligation)

    def perform_update(self, serializer):
        self._admin_guard(serializer.instance.entity)
        obligation = serializer.save()
        AuditEvent.objects.record(action="compliance.obligation_updated", actor=self.request.user, target=obligation)

    def destroy(self, request, *args, **kwargs):
        raise MethodNotAllowed("DELETE", detail="Obligations are part of the record; edit or let them lapse instead.")

    @action(detail=True, methods=["get", "post"])
    def filings(self, request, pk=None):
        """Filing tracker with evidence (FR-CMP-2); filing rolls the due date."""
        obligation = self.get_object()
        if request.method == "POST":
            self._admin_guard(obligation.entity)
            ser = FilingSerializer(data={**request.data, "obligation": obligation.pk})
            ser.is_valid(raise_exception=True)
            filing = ser.save(filed_by=request.user)
            obligation.roll_forward()
            AuditEvent.objects.record(
                action="compliance.filed", actor=request.user, target=obligation,
                metadata={"period": filing.period_label, "evidence": filing.evidence,
                          "next_due": str(obligation.due_date)},
            )
            return Response({
                "filing": FilingSerializer(filing).data,
                "next_due": obligation.due_date,
                "rag": obligation.rag,
            }, status=201)
        return Response(FilingSerializer(obligation.filings.all(), many=True).data)
