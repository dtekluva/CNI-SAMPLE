from datetime import timedelta

from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from apps.accounts.permissions import IsMFAVerified
from apps.audit.models import AuditEvent
from apps.rbac.permissions import CanAccessContent
from apps.rbac.resolution import entities_for_user, has_entity_access

from apps.rbac.resolution import is_group_admin

from .circular import ResolutionLapsed, circulate, sign
from .ctc import CTCNotAllowed, generate_ctc
from .models import DelegationRule, Resolution
from .serializers import DelegationRuleSerializer, ResolutionSerializer
from .services import cast_vote, conclude, create_resolution, results, tally


class ResolutionViewSet(viewsets.ModelViewSet):
    """Resolutions API (FR-RES-1/2/4), scoped and audited."""

    serializer_class = ResolutionSerializer
    permission_classes = [IsMFAVerified, CanAccessContent]

    def get_queryset(self):
        return Resolution.objects.filter(entity__in=entities_for_user(self.request.user))

    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        entity = ser.validated_data["entity"]
        if not has_entity_access(request.user, entity):
            raise PermissionDenied("No access to that entity.")
        res = create_resolution(
            entity=entity,
            title=ser.validated_data["title"],
            text=ser.validated_data["text"],
            mover=ser.validated_data.get("mover"),
            seconder=ser.validated_data.get("seconder"),
            meeting=ser.validated_data.get("meeting"),
            voting_mode=ser.validated_data.get("voting_mode", Resolution.VotingMode.OPEN),
            resolution_class=ser.validated_data.get("resolution_class", Resolution.ResolutionClass.ORDINARY),
            amount=ser.validated_data.get("amount"),
            category=ser.validated_data.get("category", ""),
            actor=request.user,
        )
        return Response(self.get_serializer(res).data, status=201)

    @action(detail=True, methods=["get"])
    def authority(self, request, pk=None):
        """Validate the resolution's amount/category against the DoA matrix (FR-RES-5)."""
        from .authority import authority_check

        return Response(authority_check(self.get_object()))

    @action(detail=True, methods=["post"])
    def vote(self, request, pk=None):
        from apps.conflicts.services import conflicted_user_ids

        res = self.get_object()
        # FR-VOTE-2 (checkpoint): a conflicted director cannot vote on the item.
        if res.meeting_id and request.user.pk in conflicted_user_ids(res.meeting, res.agenda_item):
            AuditEvent.objects.record(
                action="resolution.vote_blocked_recusal", actor=request.user, target=res,
                metadata={"meeting": res.meeting_id},
            )
            return Response(
                {"detail": "You have declared a conflict on this item and are recused from the vote."},
                status=409,
            )
        cast_vote(
            resolution=res, voter=request.user, choice=request.data.get("choice"),
            weight=int(request.data.get("weight", 1)),
        )
        # Mode-aware view: a secret ballot never echoes the tally back to a voter.
        return Response(results(res, viewer=request.user, is_admin=is_group_admin(request.user)))

    @action(detail=True, methods=["get"])
    def results(self, request, pk=None):
        res = self.get_object()
        return Response(results(res, viewer=request.user, is_admin=is_group_admin(request.user)))

    @action(detail=True, methods=["post"])
    def conclude(self, request, pk=None):
        res = self.get_object()
        conclude(resolution=res, actor=request.user)
        return Response(self.get_serializer(res).data)

    @action(detail=True, methods=["post"])
    def circulate(self, request, pk=None):
        res = self.get_object()
        raw = request.data.get("expires_at")
        expires_at = parse_datetime(raw) if raw else timezone.now() + timedelta(days=30)
        circulate(resolution=res, threshold=request.data.get("threshold", 1), expires_at=expires_at, actor=request.user)
        return Response(self.get_serializer(res).data)

    @action(detail=True, methods=["post"])
    def sign(self, request, pk=None):
        res = self.get_object()
        try:
            sign(resolution=res, signer=request.user)
        except ResolutionLapsed as exc:
            return Response({"detail": str(exc)}, status=409)
        res.refresh_from_db()
        return Response(self.get_serializer(res).data)

    @action(detail=True, methods=["post"])
    def ctc(self, request, pk=None):
        res = self.get_object()
        try:
            c = generate_ctc(resolution=res, issued_by=request.user)
        except CTCNotAllowed as exc:
            return Response({"detail": str(exc)}, status=409)
        return Response({"reference": c.reference, "body": c.body}, status=201)

    @action(detail=True, methods=["get"], url_path="ctc-pdf")
    def ctc_pdf(self, request, pk=None):
        from django.http import HttpResponse

        from apps.documents.pdf import render_ctc_pdf

        res = self.get_object()
        c = res.ctcs.first()
        if c is None:
            try:
                c = generate_ctc(resolution=res, issued_by=request.user)
            except CTCNotAllowed as exc:
                return Response({"detail": str(exc)}, status=409)
        resp = HttpResponse(render_ctc_pdf(ctc=c), content_type="application/pdf")
        resp["Content-Disposition"] = f'inline; filename="{c.reference.replace("/", "-")}.pdf"'
        return resp


class DelegationRuleViewSet(viewsets.ModelViewSet):
    """Delegation of Authority matrix (FR-RES-5) — scoped; cosec-only writes; audited."""

    serializer_class = DelegationRuleSerializer
    permission_classes = [IsMFAVerified, CanAccessContent]

    def get_queryset(self):
        qs = DelegationRule.objects.filter(entity__in=entities_for_user(self.request.user)).select_related("entity")
        entity = self.request.query_params.get("entity")
        if entity:
            qs = qs.filter(entity_id=entity)
        return qs

    def _guard(self, entity):
        if not has_entity_access(self.request.user, entity):
            raise PermissionDenied("No access to that entity.")
        if not is_group_admin(self.request.user):
            raise PermissionDenied("Only the Company Secretary maintains the delegation-of-authority matrix.")

    def perform_create(self, serializer):
        self._guard(serializer.validated_data["entity"])
        rule = serializer.save()
        AuditEvent.objects.record(action="doa.rule_created", actor=self.request.user, target=rule.entity,
                                  metadata={"category": rule.category, "approver": rule.approver, "limit": str(rule.max_amount)})

    def perform_update(self, serializer):
        self._guard(serializer.instance.entity)
        serializer.save()

    def perform_destroy(self, instance):
        self._guard(instance.entity)
        AuditEvent.objects.record(action="doa.rule_removed", actor=self.request.user, target=instance.entity,
                                  metadata={"category": instance.category})
        instance.delete()
