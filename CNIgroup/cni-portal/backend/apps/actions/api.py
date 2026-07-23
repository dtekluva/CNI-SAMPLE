from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action as drf_action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from apps.accounts.permissions import IsMFAVerified
from apps.rbac.permissions import CanAccessContent
from apps.rbac.resolution import entities_for_user, has_entity_access

from .models import Action
from .serializers import ActionSerializer
from .services import complete_action, create_action


class ActionViewSet(viewsets.ModelViewSet):
    """Actions API (FR-ACT-1), scoped; ?mine=true and ?overdue=true filters."""

    serializer_class = ActionSerializer
    permission_classes = [IsMFAVerified, CanAccessContent]

    def get_queryset(self):
        qs = Action.objects.filter(entity__in=entities_for_user(self.request.user))
        if self.request.query_params.get("mine") == "true":
            qs = qs.filter(owner=self.request.user)
        if self.request.query_params.get("overdue") == "true":
            qs = qs.filter(status=Action.Status.OPEN, due_date__lt=timezone.now().date())
        return qs

    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        entity = ser.validated_data["entity"]
        if not has_entity_access(request.user, entity):
            raise PermissionDenied("No access to that entity.")
        a = create_action(
            entity=entity,
            title=ser.validated_data["title"],
            owner=ser.validated_data.get("owner"),
            owner_name=ser.validated_data.get("owner_name", ""),
            due_date=ser.validated_data.get("due_date"),
            meeting=ser.validated_data.get("meeting"),
            agenda_item=ser.validated_data.get("agenda_item"),
            actor=request.user,
        )
        return Response(self.get_serializer(a).data, status=201)

    @drf_action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        a = self.get_object()
        complete_action(action=a, evidence=request.data.get("evidence", ""), actor=request.user)
        return Response(self.get_serializer(a).data)

    @drf_action(detail=False, methods=["post"], url_path="run-reminders")
    def run_reminders(self, request):
        """
        FR-ACT-2: remind owners of actions due within 7 days, and escalate
        overdue ones to the Company Secretary. Returns what was sent. (In-portal
        notifications; real delivery stays env-gated.)
        """
        from datetime import timedelta

        from apps.notifications.services import notify
        from apps.rbac.models import Role, RoleAssignment

        today = timezone.now().date()
        scope = entities_for_user(request.user)
        soon = Action.objects.filter(entity__in=scope, status=Action.Status.OPEN,
                                     due_date__gte=today, due_date__lte=today + timedelta(days=7))
        overdue = Action.objects.filter(entity__in=scope, status=Action.Status.OPEN, due_date__lt=today)

        reminded = escalated = 0
        for a in soon.select_related("owner"):
            if a.owner_id:
                notify(recipient=a.owner, event_type="action.due_soon",
                       subject=f"Action due soon: {a.title}", link=f"/actions")
                reminded += 1
        # escalate overdue to group cosecs
        cosecs = {ra.user for ra in RoleAssignment.objects.filter(
            role=Role.COMPANY_SECRETARY, entity__isnull=True).select_related("user")}
        for a in overdue:
            for cosec in cosecs:
                notify(recipient=cosec, event_type="action.escalated",
                       subject=f"Overdue action escalated: {a.title}", link="/actions")
                escalated += 1
        return Response({"reminded": reminded, "escalated": escalated})

    @drf_action(detail=False, methods=["get"], url_path="overdue-dashboard")
    def overdue_dashboard(self, request):
        """FR-ACT-3: open actions grouped by entity and owner, with age."""
        today = timezone.now().date()
        qs = (Action.objects.filter(entity__in=entities_for_user(request.user), status=Action.Status.OPEN)
              .select_related("entity", "owner").order_by("due_date"))
        groups = {}
        for a in qs:
            key = a.entity.legal_name
            g = groups.setdefault(key, {"entity": a.entity_id, "entity_name": key, "items": []})
            age = (today - a.due_date).days if a.due_date and a.due_date < today else None
            g["items"].append({
                "id": a.id, "title": a.title,
                "owner": a.owner.name or a.owner.email if a.owner_id else (a.owner_name or "Unassigned"),
                "due_date": a.due_date, "overdue_days": age,
            })
        return Response(list(groups.values()))
