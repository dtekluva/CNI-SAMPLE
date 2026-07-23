from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.accounts.permissions import IsMFAVerified

from .dashboard import dashboard_for


@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    """Liveness probe — the one deliberately public endpoint."""
    return Response({"status": "ok", "service": "cni-governance-api", "version": "0.1.0"})


@api_view(["GET"])
@permission_classes([IsMFAVerified])
def dashboard(request):
    """Permission-scoped role dashboard summary (FR-RPT-2)."""
    return Response(dashboard_for(request.user))


@api_view(["GET"])
@permission_classes([IsMFAVerified])
def global_search_view(request):
    """FR-RPT-1 (checkpoint): one permission-scoped search across all record types."""
    from .search import global_search

    q = request.query_params.get("q", "").strip()
    if len(q) < 2:
        return Response({"q": q, "results": []})
    return Response({"q": q, "results": global_search(request.user, q)})


@api_view(["GET"])
@permission_classes([IsMFAVerified])
def export_view(request, kind):
    """FR-RPT-3: statutory exports as dated, entity-branded PDFs (cosec only)."""
    from django.http import HttpResponse

    from apps.audit.models import AuditEvent
    from apps.entities.models import Entity
    from apps.rbac.resolution import entities_for_user, is_group_admin

    from .exports import RENDERERS

    if not is_group_admin(request.user):
        return Response({"detail": "Only a group administrator may export statutory records."}, status=403)
    renderer = RENDERERS.get(kind)
    if renderer is None:
        return Response({"detail": f"Unknown export '{kind}'."}, status=404)
    entity = entities_for_user(request.user).filter(pk=request.query_params.get("entity")).first()
    if entity is None:
        return Response({"detail": "entity parameter required (and in scope)."}, status=400)
    AuditEvent.objects.record(action="export.generated", actor=request.user, target=entity,
                              metadata={"kind": kind})
    pdf = renderer(entity, request.user)
    resp = HttpResponse(pdf, content_type="application/pdf")
    resp["Content-Disposition"] = f'inline; filename="{kind}-{entity.pk}.pdf"'
    return resp
