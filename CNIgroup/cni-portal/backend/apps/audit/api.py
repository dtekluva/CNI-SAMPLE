from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from apps.accounts.permissions import IsMFAVerified
from apps.rbac.resolution import is_group_admin

from .models import AuditEvent
from .serializers import AuditEventSerializer


class AuditEventViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Audit log API (NFR-AUD-1): read-only export, filterable. Group admins see the
    whole log; everyone else sees only their own attributed trail.
    """

    serializer_class = AuditEventSerializer
    permission_classes = [IsMFAVerified]

    def get_queryset(self):
        if is_group_admin(self.request.user):
            qs = AuditEvent.objects.all()
        else:
            qs = AuditEvent.objects.filter(actor=self.request.user)

        params = self.request.query_params
        if params.get("action"):
            qs = qs.filter(action=params["action"])
        if params.get("since"):
            qs = qs.filter(timestamp__gte=params["since"])
        if params.get("until"):
            qs = qs.filter(timestamp__lte=params["until"])
        return qs.order_by("-id")


@api_view(["GET"])
@permission_classes([IsMFAVerified])
def integrity(request):
    """Full record-integrity report (NFR-INT-1) — group admins only; audited."""
    from apps.rbac.resolution import is_group_admin

    from .integrity import integrity_report

    if not is_group_admin(request.user):
        return Response({"detail": "Only a group administrator may run integrity verification."}, status=403)
    report = integrity_report()
    AuditEvent.objects.record(action="integrity.verified", actor=request.user,
                              metadata={"all_intact": report["all_intact"]})
    return Response(report)
