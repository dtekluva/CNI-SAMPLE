from django.contrib.auth import get_user_model
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from apps.accounts.permissions import IsMFAVerified
from apps.audit.models import AuditEvent
from apps.rbac.permissions import CanAccessContent
from apps.rbac.resolution import entities_for_user, has_entity_access

from .agenda import add_item, reorder_items, table_of_contents
from .attendance import quorum_status
from .models import AgendaItem, Meeting
from .notice import ShortNoticeError, dispatch_notice, record_consent_to_short_notice
from .serializers import AgendaItemSerializer, MeetingSerializer


class MeetingViewSet(viewsets.ModelViewSet):
    """Meetings API (FR-MTG-1/2/5), permission-scoped and audited."""

    serializer_class = MeetingSerializer
    permission_classes = [IsMFAVerified, CanAccessContent]

    def get_queryset(self):
        return Meeting.objects.filter(entity__in=entities_for_user(self.request.user))

    def perform_create(self, serializer):
        entity = serializer.validated_data["entity"]
        if not has_entity_access(self.request.user, entity):
            raise PermissionDenied("No access to that entity.")
        meeting = serializer.save()
        AuditEvent.objects.record(action="meeting.created", actor=self.request.user, target=meeting)

    @action(detail=True, methods=["get"])
    def quorum(self, request, pk=None):
        return Response(quorum_status(self.get_object()))

    @action(detail=True, methods=["post"])
    def dispatch_notice(self, request, pk=None):
        meeting = self.get_object()
        recipients = list(get_user_model().objects.filter(id__in=request.data.get("recipients", [])))
        try:
            proofs = dispatch_notice(actor=request.user, meeting=meeting, recipients=recipients)
        except ShortNoticeError as exc:
            return Response({"detail": str(exc)}, status=409)
        return Response({"dispatched": len(proofs)})

    @action(detail=True, methods=["post"], url_path="consent-short-notice")
    def consent_short_notice(self, request, pk=None):
        meeting = self.get_object()
        record_consent_to_short_notice(actor=request.user, meeting=meeting, member=request.user)
        return Response({"ok": True})

    @action(detail=True, methods=["get"])
    def toc(self, request, pk=None):
        return Response(table_of_contents(self.get_object()))

    @action(detail=True, methods=["get", "post"])
    def agenda(self, request, pk=None):
        meeting = self.get_object()
        if request.method == "POST":
            ser = AgendaItemSerializer(data=request.data)
            ser.is_valid(raise_exception=True)
            d = ser.validated_data
            item = add_item(
                meeting=meeting,
                title=d["title"],
                item_type=d.get("item_type", AgendaItem.ItemType.DISCUSSION),
                owner=d.get("owner"),
                time_allocation_minutes=d.get("time_allocation_minutes", 0),
            )
            return Response(AgendaItemSerializer(item).data, status=201)
        return Response(AgendaItemSerializer(meeting.agenda_items.all(), many=True).data)

    @action(detail=True, methods=["post"], url_path="agenda/reorder")
    def agenda_reorder(self, request, pk=None):
        meeting = self.get_object()
        reorder_items(meeting=meeting, ordered_ids=request.data.get("ordered_ids", []))
        return Response(table_of_contents(meeting))

    @action(detail=True, methods=["get", "post"], url_path="matters-arising")
    def matters_arising(self, request, pk=None):
        """
        Matters arising auto-carry (FR-MIN-4): open actions from prior meetings.
        GET previews them; POST plants the 'Matters arising' item into the agenda.
        """
        from .agenda import MATTERS_ARISING_TITLE, ensure_matters_arising, open_prior_actions

        meeting = self.get_object()
        actions = [
            {
                "id": a.id, "title": a.title, "owner_name": a.owner_name,
                "due_date": a.due_date, "status": a.status,
                "source_meeting": a.meeting.title if a.meeting_id else None,
            }
            for a in open_prior_actions(meeting)
        ]
        on_agenda = meeting.agenda_items.filter(title=MATTERS_ARISING_TITLE).exists()
        if request.method == "POST":
            _, created = ensure_matters_arising(meeting=meeting, actor=request.user)
            on_agenda = True
            if created:
                AuditEvent.objects.record(
                    action="agenda.matters_arising_added", actor=request.user, target=meeting,
                    metadata={"carried": len(actions)},
                )
        return Response({"on_agenda": on_agenda, "actions": actions})

    @action(detail=True, methods=["get", "post"], url_path="offline-pack")
    def offline_pack(self, request, pk=None):
        """
        Offline pack grants (FR-DOC-6). POST takes/refreshes my offline copy;
        GET returns its status. A wiped/revoked grant tells my device to wipe.
        """
        from apps.documents.models import OfflinePackGrant
        from apps.documents.serializers import OfflineGrantSerializer

        meeting = self.get_object()
        if request.method == "POST":
            grant, _ = OfflinePackGrant.objects.update_or_create(
                meeting=meeting, user=request.user,
                defaults={"device": request.data.get("device", ""),
                          "status": OfflinePackGrant.Status.ACTIVE, "revoked_at": None},
            )
            AuditEvent.objects.record(action="offline.pack_downloaded", actor=request.user, target=meeting)
            return Response(OfflineGrantSerializer(grant).data, status=201)
        grant = meeting.offline_grants.filter(user=request.user).first()
        return Response(OfflineGrantSerializer(grant).data if grant else {"status": "none"})

    @action(detail=True, methods=["post"], url_path="offline-pack/sync")
    def offline_pack_sync(self, request, pk=None):
        """Device sync (FR-DOC-6): if my grant was revoked, confirm the local wipe."""
        from django.utils import timezone

        from apps.documents.models import OfflinePackGrant

        meeting = self.get_object()
        grant = meeting.offline_grants.filter(user=request.user).first()
        if grant is None:
            return Response({"wipe": True, "reason": "no grant"})
        grant.synced_at = timezone.now()
        wipe = grant.status in (OfflinePackGrant.Status.REVOKED, OfflinePackGrant.Status.WIPED)
        if grant.status == OfflinePackGrant.Status.REVOKED:
            grant.status = OfflinePackGrant.Status.WIPED
        grant.save(update_fields=["synced_at", "status"])
        return Response({"wipe": wipe, "status": grant.status})

    @action(detail=True, methods=["post"], url_path="wipe-packs")
    def wipe_packs(self, request, pk=None):
        """Remote-wipe every offline copy of this meeting's pack (cosec/admin)."""
        from apps.documents.lifecycle import wipe_meeting_packs
        from apps.rbac.resolution import is_group_admin

        meeting = self.get_object()
        if not is_group_admin(request.user):
            return Response({"detail": "Only the Company Secretary may wipe packs."}, status=403)
        n = wipe_meeting_packs(meeting=meeting, actor=request.user)
        return Response({"revoked": n})

    @action(detail=False, methods=["get"], url_path="group-summary")
    def group_summary(self, request):
        """Group vs entity rollup across everything the caller can see (FR-ENT-2)."""
        from .sessions import group_summary

        return Response(group_summary(request.user))

    @action(detail=True, methods=["get", "post"], url_path="in-meeting")
    def in_meeting(self, request, pk=None):
        """In-meeting mode (FR-MTG-7). GET = live state; POST {action} = start/present/end."""
        from .sessions import end_session, present_item, session_state, start_session

        meeting = self.get_object()
        if request.method == "POST":
            act = request.data.get("action")
            if act == "start":
                start_session(meeting)
                AuditEvent.objects.record(action="meeting.session_started", actor=request.user, target=meeting)
            elif act == "present":
                item = meeting.agenda_items.filter(pk=request.data.get("item")).first()
                if not item:
                    return Response({"detail": "No such agenda item."}, status=404)
                present_item(meeting, item)
            elif act == "end":
                end_session(meeting)
                AuditEvent.objects.record(action="meeting.session_ended", actor=request.user, target=meeting)
            else:
                return Response({"detail": "action must be start | present | end."}, status=400)
        return Response(session_state(meeting))

    @action(detail=True, methods=["get", "post"], url_path="minutes")
    def minutes(self, request, pk=None):
        from apps.minutes.serializers import MinutesSerializer
        from apps.minutes.services import seed_minutes

        m = seed_minutes(meeting=self.get_object())  # idempotent
        return Response(MinutesSerializer(m).data, status=201 if request.method == "POST" else 200)

    @action(detail=True, methods=["post"], url_path="minutes/transition")
    def minutes_transition(self, request, pk=None):
        from apps.minutes.serializers import MinutesSerializer
        from apps.minutes.services import seed_minutes
        from apps.minutes.workflow import TransitionError, UndispositionedComments, transition

        m = seed_minutes(meeting=self.get_object())
        try:
            transition(actor=request.user, minutes=m, to_state=request.data.get("to_state"))
        except UndispositionedComments as exc:
            return Response({"detail": str(exc)}, status=409)
        except TransitionError as exc:
            return Response({"detail": str(exc)}, status=400)
        return Response(MinutesSerializer(m).data)

    @action(detail=True, methods=["post"], url_path="minutes/block")
    def minutes_block(self, request, pk=None):
        """Write minute text for one agenda item (FR-MIN-1); locked after adoption."""
        from apps.minutes.models import MinuteBlock
        from apps.minutes.serializers import MinuteBlockSerializer
        from apps.minutes.services import MinutesLocked, seed_minutes, update_block

        m = seed_minutes(meeting=self.get_object())
        try:
            block = m.blocks.get(pk=request.data.get("block"))
        except MinuteBlock.DoesNotExist:
            return Response({"detail": "No such block on these minutes."}, status=404)
        try:
            update_block(actor=request.user, block=block, text=str(request.data.get("text", "")))
        except MinutesLocked as exc:
            return Response({"detail": str(exc)}, status=409)
        return Response(MinuteBlockSerializer(block).data)

    @action(detail=True, methods=["post"], url_path="minutes/comment")
    def minutes_comment(self, request, pk=None):
        from apps.minutes.services import seed_minutes
        from apps.minutes.workflow import add_comment

        m = seed_minutes(meeting=self.get_object())
        add_comment(minutes=m, author=request.user, text=request.data.get("text", ""))
        return Response({"ok": True}, status=201)

    @action(detail=True, methods=["get", "post"])
    def pack(self, request, pk=None):
        from apps.documents.packs import build_toc, compile_pack

        meeting = self.get_object()
        if request.method == "POST":
            result = compile_pack(meeting=meeting, actor=request.user)
            return Response(
                {"version": result["pack"].version_number, "toc": result["toc"], "total_pages": result["total_pages"]},
                status=201,
            )
        toc, total = build_toc(meeting)
        latest = meeting.board_packs.first()
        return Response({"latest_version": latest.version_number if latest else 0, "toc": toc, "total_pages": total})

    @action(detail=True, methods=["get"], url_path="pack-pdf")
    def pack_pdf(self, request, pk=None):
        from django.http import HttpResponse

        from apps.documents.delivery import watermark_for
        from apps.documents.pdf import render_pack_pdf

        meeting = self.get_object()
        pdf = render_pack_pdf(meeting=meeting, watermark=watermark_for(request.user))
        resp = HttpResponse(pdf, content_type="application/pdf")
        resp["Content-Disposition"] = f'inline; filename="pack-{meeting.id}.pdf"'
        return resp
