"""
Committees API (FR-COM-1/2/3) — scoped to the caller's entities; committee
structure is managed by the cosec (group admin), reports flow to the board.
"""
from datetime import date

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import MethodNotAllowed, PermissionDenied
from rest_framework.response import Response
from rest_framework.serializers import DateField

from apps.accounts.permissions import IsMFAVerified
from apps.audit.models import AuditEvent
from apps.rbac.permissions import CanAccessContent
from apps.rbac.resolution import entities_for_user, has_entity_access, is_group_admin

from .models import Committee, CommitteeMembership, CommitteeReport
from .serializers import CommitteeSerializer, MembershipSerializer, ReportSerializer


class CommitteeViewSet(viewsets.ModelViewSet):
    serializer_class = CommitteeSerializer
    permission_classes = [IsMFAVerified, CanAccessContent]

    def get_queryset(self):
        return (
            Committee.objects.filter(entity__in=entities_for_user(self.request.user))
            .select_related("entity")
            .prefetch_related("memberships__user")
        )

    def _admin_guard(self, entity):
        if not has_entity_access(self.request.user, entity):
            raise PermissionDenied("No access to that entity.")
        if not is_group_admin(self.request.user):
            raise PermissionDenied("Only the Company Secretary manages committee structure.")

    def perform_create(self, serializer):
        self._admin_guard(serializer.validated_data["entity"])
        committee = serializer.save()
        AuditEvent.objects.record(action="committee.created", actor=self.request.user, target=committee)

    def perform_update(self, serializer):
        self._admin_guard(serializer.instance.entity)
        committee = serializer.save()
        AuditEvent.objects.record(action="committee.updated", actor=self.request.user, target=committee)

    def destroy(self, request, *args, **kwargs):
        raise MethodNotAllowed("DELETE", detail="Committees are part of the record; disband by ending memberships.")

    @action(detail=True, methods=["post"])
    def appoint(self, request, pk=None):
        """Appoint a member with a term (FR-COM-2)."""
        committee = self.get_object()
        self._admin_guard(committee.entity)
        ser = MembershipSerializer(data={**request.data, "committee": committee.pk})
        ser.is_valid(raise_exception=True)
        membership = ser.save()
        AuditEvent.objects.record(
            action="committee.member_appointed", actor=request.user, target=committee,
            metadata={"user": membership.user_id, "role": membership.role, "term_end": str(membership.term_end or "")},
        )
        return Response(MembershipSerializer(membership).data, status=201)

    @action(detail=True, methods=["post"], url_path="end-membership")
    def end_membership(self, request, pk=None):
        """Rotate a member off (FR-COM-2) — end-dated, never deleted."""
        committee = self.get_object()
        self._admin_guard(committee.entity)
        try:
            membership = committee.memberships.get(pk=request.data.get("membership"))
        except CommitteeMembership.DoesNotExist:
            return Response({"detail": "No such membership."}, status=404)
        on = request.data.get("ended_on") or date.today().isoformat()
        membership.ended_on = DateField().to_internal_value(on)
        membership.save(update_fields=["ended_on"])
        AuditEvent.objects.record(
            action="committee.member_rotated", actor=request.user, target=committee,
            metadata={"membership": membership.pk, "ended_on": str(on)},
        )
        return Response({"ended_on": on})

    @action(detail=True, methods=["get", "post"])
    def reports(self, request, pk=None):
        """Committee-to-board reporting (FR-COM-3)."""
        committee = self.get_object()
        if request.method == "POST":
            ser = ReportSerializer(data={**request.data, "committee": committee.pk})
            ser.is_valid(raise_exception=True)
            report = ser.save(submitted_by=request.user)
            AuditEvent.objects.record(action="committee.report_submitted", actor=request.user, target=report)
            return Response(ReportSerializer(report).data, status=201)
        return Response(ReportSerializer(committee.reports.all(), many=True).data)

    @action(detail=True, methods=["post"], url_path="note-report")
    def note_report(self, request, pk=None):
        """The board formally notes a committee report (FR-COM-3)."""
        from django.utils import timezone

        committee = self.get_object()
        self._admin_guard(committee.entity)
        try:
            report = committee.reports.get(pk=request.data.get("report"))
        except CommitteeReport.DoesNotExist:
            return Response({"detail": "No such report."}, status=404)
        report.status = CommitteeReport.Status.NOTED
        report.noted_at = timezone.now()
        report.save(update_fields=["status", "noted_at"])
        AuditEvent.objects.record(action="committee.report_noted", actor=request.user, target=report)
        return Response(ReportSerializer(report).data)
