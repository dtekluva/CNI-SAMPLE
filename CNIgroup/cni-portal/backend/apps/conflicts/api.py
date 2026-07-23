"""
Interests & conflicts API (FR-CONF-1/2) — checkpoint.

A director declares their OWN interests and conflicts (director field is always
the caller). Reading is scoped: group admins / cosec see every declaration in
their entities; a director sees their own. Withdrawal end-dates, never deletes.
"""
from datetime import date

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import MethodNotAllowed, PermissionDenied
from rest_framework.response import Response

from apps.accounts.permissions import IsMFAVerified
from apps.rbac.permissions import CanAccessContent
from apps.rbac.resolution import entities_for_user, has_entity_access, is_group_admin

from .models import ConflictDeclaration, InterestDeclaration
from .serializers import ConflictSerializer, InterestSerializer
from .services import declare_conflict, declare_interest, withdraw_interest


class InterestViewSet(viewsets.ModelViewSet):
    serializer_class = InterestSerializer
    permission_classes = [IsMFAVerified, CanAccessContent]

    def get_queryset(self):
        qs = InterestDeclaration.objects.filter(entity__in=entities_for_user(self.request.user))
        if not is_group_admin(self.request.user):
            qs = qs.filter(director=self.request.user)
        if self.request.query_params.get("active") == "true":
            qs = qs.filter(withdrawn_on__isnull=True)
        return qs

    def perform_create(self, serializer):
        entity = serializer.validated_data["entity"]
        if not has_entity_access(self.request.user, entity):
            raise PermissionDenied("No access to that entity.")
        declare_interest(
            actor=self.request.user, entity=entity, director=self.request.user,
            kind=serializer.validated_data["kind"], party=serializer.validated_data["party"],
            declared_on=serializer.validated_data["declared_on"],
            details=serializer.validated_data.get("details", ""),
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({"ok": True}, status=201)

    def destroy(self, request, *args, **kwargs):
        raise MethodNotAllowed("DELETE", detail="Interests are withdrawn (end-dated), not deleted.")

    @action(detail=True, methods=["post"])
    def withdraw(self, request, pk=None):
        interest = self.get_object()
        if interest.director_id != request.user.pk and not is_group_admin(request.user):
            raise PermissionDenied("Only the declaring director (or cosec) may withdraw.")
        on = request.data.get("withdrawn_on") or date.today().isoformat()
        withdraw_interest(actor=request.user, interest=interest, on=on)
        return Response({"withdrawn_on": on})


class ConflictViewSet(viewsets.ModelViewSet):
    serializer_class = ConflictSerializer
    permission_classes = [IsMFAVerified, CanAccessContent]

    def get_queryset(self):
        qs = ConflictDeclaration.objects.filter(meeting__entity__in=entities_for_user(self.request.user))
        meeting = self.request.query_params.get("meeting")
        if meeting:
            qs = qs.filter(meeting_id=meeting)
        if not is_group_admin(self.request.user):
            qs = qs.filter(director=self.request.user)
        return qs

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        meeting = serializer.validated_data["meeting"]
        if not has_entity_access(request.user, meeting.entity):
            raise PermissionDenied("No access to that meeting's entity.")
        declare_conflict(
            actor=request.user, meeting=meeting, director=request.user,
            agenda_item=serializer.validated_data.get("agenda_item"),
            interest=serializer.validated_data.get("interest"),
            note=serializer.validated_data.get("note", ""),
        )
        return Response({"ok": True}, status=201)

    def destroy(self, request, *args, **kwargs):
        raise MethodNotAllowed("DELETE", detail="Conflict declarations are part of the record.")
