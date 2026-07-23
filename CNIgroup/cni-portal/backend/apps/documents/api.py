from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from apps.accounts.permissions import IsMFAVerified
from apps.audit.models import AuditEvent
from apps.conflicts.services import exclude_recused_documents
from apps.rbac.permissions import CanAccessContent
from apps.rbac.resolution import entities_for_user, has_entity_access, is_group_admin

from .delivery import DownloadNotAllowed, request_download, watermark_for
from .models import Document
from .serializers import AnnotationSerializer, DocumentSerializer
from .services import search_documents


class DocumentViewSet(viewsets.ModelViewSet):
    """Documents API (FR-DOC-1/2/3), scoped; download control + watermark."""

    serializer_class = DocumentSerializer
    permission_classes = [IsMFAVerified, CanAccessContent]

    def get_queryset(self):
        qs = Document.objects.filter(entity__in=entities_for_user(self.request.user))
        # FR-RBAC-2: item-level recusal overrides entity inheritance. The cosec
        # (group admin) retains record-keeper access to assemble packs.
        if not is_group_admin(self.request.user):
            qs = exclude_recused_documents(qs, self.request.user)
        return qs

    def perform_create(self, serializer):
        entity = serializer.validated_data["entity"]
        if not has_entity_access(self.request.user, entity):
            raise PermissionDenied("No access to that entity.")
        doc = serializer.save()
        AuditEvent.objects.record(action="document.created", actor=self.request.user, target=doc)

    @action(detail=True, methods=["get"])
    def download(self, request, pk=None):
        doc = self.get_object()
        try:
            url = request_download(doc, request.user)
        except DownloadNotAllowed as exc:
            return Response({"detail": str(exc)}, status=409)
        AuditEvent.objects.record(action="document.download_requested", actor=request.user, target=doc)
        return Response({"url": url, "watermark": watermark_for(request.user)})

    @action(detail=False, methods=["get"])
    def search(self, request):
        docs = search_documents(user=request.user, query=request.query_params.get("q", ""))
        return Response(DocumentSerializer(docs, many=True).data)

    # ---- Lifecycle: retention, legal hold, secure purge (FR-DOC-5) ----
    @action(detail=False, methods=["get"], url_path="purge-eligible")
    def purge_eligible_list(self, request):
        from .lifecycle import purge_eligible

        if not is_group_admin(request.user):
            raise PermissionDenied("Only the Company Secretary manages retention.")
        qs = purge_eligible(self.get_queryset())
        return Response(DocumentSerializer(qs, many=True).data)

    @action(detail=True, methods=["post"], url_path="legal-hold")
    def legal_hold(self, request, pk=None):
        from .lifecycle import set_legal_hold

        doc = self.get_object()
        if not is_group_admin(request.user):
            raise PermissionDenied("Only the Company Secretary manages legal holds.")
        set_legal_hold(document=doc, on=bool(request.data.get("on", True)), actor=request.user)
        return Response(DocumentSerializer(doc).data)

    @action(detail=True, methods=["post"])
    def purge(self, request, pk=None):
        from .lifecycle import purge_document

        doc = self.get_object()
        if not is_group_admin(request.user):
            raise PermissionDenied("Only the Company Secretary may purge documents.")
        try:
            cert = purge_document(document=doc, actor=request.user, reason=request.data.get("reason", ""))
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=409)
        return Response({
            "purged": True,
            "certificate": {"reference": cert.reference, "content_hash": cert.content_hash,
                            "certified_at": cert.certified_at},
        }, status=200)

    @action(detail=True, methods=["get"])
    def content(self, request, pk=None):
        """Latest-version text for the in-portal reader (FR-DOC-1); view is audited."""
        doc = self.get_object()
        latest = doc.versions.first()
        AuditEvent.objects.record(action="document.viewed", actor=request.user, target=doc)
        return Response({
            "id": doc.id,
            "title": doc.title,
            "text": latest.text_content if latest else "",
            "version": latest.version_number if latest else 0,
            "versions": [
                {"version_number": v.version_number, "uploaded_at": v.uploaded_at, "content_hash": v.content_hash[:12]}
                for v in doc.versions.all()
            ],
            "watermark": watermark_for(request.user),
        })

    @action(detail=True, methods=["get"])
    def pdf(self, request, pk=None):
        """The document rendered as a watermarked PDF, viewable in-browser (FR-DOC-3)."""
        from django.http import HttpResponse

        from .pdf import render_document_pdf

        doc = self.get_object()
        AuditEvent.objects.record(action="document.viewed", actor=request.user, target=doc,
                                  metadata={"format": "pdf"})
        pdf_bytes = render_document_pdf(document=doc, watermark=watermark_for(request.user))
        resp = HttpResponse(pdf_bytes, content_type="application/pdf")
        resp["Content-Disposition"] = f'inline; filename="document-{doc.id}.pdf"'
        return resp


class AnnotationViewSet(viewsets.ModelViewSet):
    """
    Paper annotations (FR-DOC-4). A user sees their own notes plus notes shared
    with them; visibility is enforced server-side. Author is always the caller.
    """

    serializer_class = AnnotationSerializer
    permission_classes = [IsMFAVerified, CanAccessContent]

    def get_queryset(self):
        from django.db.models import Q

        from .models import Annotation

        scope = entities_for_user(self.request.user)
        qs = Annotation.objects.filter(document__entity__in=scope).select_related("author")
        # own notes + notes explicitly shared with me
        qs = qs.filter(Q(author=self.request.user) | Q(shared_with=self.request.user)).distinct()
        doc = self.request.query_params.get("document")
        if doc:
            qs = qs.filter(document_id=doc)
        return qs

    def create(self, request, *args, **kwargs):
        from .models import Document

        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        doc = Document.objects.filter(pk=request.data.get("document")).first()
        if doc is None or not has_entity_access(request.user, doc.entity):
            raise PermissionDenied("No access to that document.")
        ann = ser.save(author=request.user, document=doc)
        if request.data.get("shared_with"):
            ann.shared_with.set(request.data["shared_with"])
        AuditEvent.objects.record(action="annotation.created", actor=request.user, target=doc,
                                  metadata={"visibility": ann.visibility})
        return Response(self.get_serializer(ann).data, status=201)

    def perform_destroy(self, instance):
        if instance.author_id != self.request.user.pk:
            raise PermissionDenied("You can only delete your own annotations.")
        instance.delete()
