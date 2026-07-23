"""
Statutory registers API (FR-ENT-3) — permission-scoped and audited (checkpoint).

Scoped to the caller's entities. Only a Company Secretary / Super Administrator
may write (maintaining statutory registers is the cosec's duty). Entries cannot
be destroyed via the API — a party is *ceased*, preserving the historical record.
"""
from datetime import date

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import MethodNotAllowed, PermissionDenied
from rest_framework.response import Response

from apps.accounts.permissions import IsMFAVerified
from apps.audit.models import AuditEvent
from apps.rbac.models import Role
from apps.rbac.permissions import CanAccessContent
from apps.rbac.resolution import entities_for_user, has_entity_access, has_role, is_group_admin

from .models import RegisterEntry
from .serializers import RegisterEntrySerializer
from .services import cease_entry, entries_as_at


def _can_maintain(user, entity):
    return is_group_admin(user) or has_role(user, entity, Role.COMPANY_SECRETARY, Role.SUPER_ADMIN)


class RegisterEntryViewSet(viewsets.ModelViewSet):
    serializer_class = RegisterEntrySerializer
    permission_classes = [IsMFAVerified, CanAccessContent]

    def get_queryset(self):
        qs = RegisterEntry.objects.filter(entity__in=entities_for_user(self.request.user))
        rt = self.request.query_params.get("register_type")
        if rt:
            qs = qs.filter(register_type=rt)
        entity = self.request.query_params.get("entity")
        if entity:
            qs = qs.filter(entity_id=entity)
        active = self.request.query_params.get("active")
        if active == "true":
            qs = qs.filter(ceased_on__isnull=True)
        as_at = self.request.query_params.get("as_at")
        if as_at:
            qs = entries_as_at(qs, as_at)
        return qs

    def _guard(self, entity):
        if not has_entity_access(self.request.user, entity):
            raise PermissionDenied("No access to that entity.")
        if not _can_maintain(self.request.user, entity):
            raise PermissionDenied("Only the Company Secretary may maintain statutory registers.")

    def perform_create(self, serializer):
        self._guard(serializer.validated_data["entity"])
        entry = serializer.save()
        AuditEvent.objects.record(
            action="register.entry.added",
            actor=self.request.user,
            target=entry,
            metadata={"register": entry.register_type},
        )

    def perform_update(self, serializer):
        self._guard(serializer.instance.entity)
        entry = serializer.save()
        AuditEvent.objects.record(action="register.entry.updated", actor=self.request.user, target=entry)

    def destroy(self, request, *args, **kwargs):
        raise MethodNotAllowed(
            "DELETE", detail="Statutory register entries cannot be deleted; cease the entry instead."
        )

    @action(detail=True, methods=["post"])
    def cease(self, request, pk=None):
        entry = self.get_object()
        self._guard(entry.entity)
        on = request.data.get("ceased_on") or date.today().isoformat()
        cease_entry(actor=request.user, entry=entry, on=on)
        return Response({"ceased_on": on})

    @action(detail=False, methods=["get"])
    def directors(self, request):
        """
        Directors roster (FR-CONF-1 groundwork): the register of directors joined
        with each director's shareholding from the register of members, per entity.
        """
        scope = entities_for_user(request.user)
        directors = RegisterEntry.objects.filter(entity__in=scope, register_type="directors").select_related("entity")
        members = RegisterEntry.objects.filter(entity__in=scope, register_type="members")
        holding = {(m.entity_id, m.party_name): m for m in members}

        roster = []
        for d in directors:
            m = holding.get((d.entity_id, d.party_name))
            particulars = d.particulars or {}
            roster.append({
                "id": d.id,
                "entity": d.entity_id,
                "entity_name": d.entity.legal_name,
                "name": d.party_name,
                "designation": particulars.get("designation", "Director"),
                "appointed": d.effective_from,
                "ceased_on": d.ceased_on,
                "active": d.ceased_on is None,
                "shares": (m.particulars or {}).get("shares") if m else None,
                "share_class": (m.particulars or {}).get("class") if m else None,
            })
        roster.sort(key=lambda r: (r["entity_name"], not r["active"], r["name"]))
        return Response(roster)

    @action(detail=True, methods=["get"])
    def director(self, request, pk=None):
        """
        Full director profile from the directors-register entry: identity, KYC
        document, contact, shareholding. BVN is masked unless the caller is a
        group admin; every profile view is audited (NFR-AUD-1).
        """
        entry = self.get_object()
        if entry.register_type != "directors":
            return Response({"detail": "Not a directors-register entry."}, status=404)
        p = dict(entry.particulars or {})

        admin = is_group_admin(request.user)
        bvn = p.get("bvn")
        if bvn and not admin:
            bvn = f"•••••••{str(bvn)[-4:]}"  # least-privilege: last 4 only

        member = RegisterEntry.objects.filter(
            entity=entry.entity, register_type="members", party_name=entry.party_name
        ).first()
        AuditEvent.objects.record(
            action="register.director.viewed", actor=request.user, target=entry,
            metadata={"bvn_unmasked": bool(p.get("bvn")) and admin},
        )
        return Response({
            "id": entry.id,
            "entity": entry.entity_id,
            "entity_name": entry.entity.legal_name,
            "name": p.get("full_name") or entry.party_name,
            "designation": p.get("designation", "Director"),
            "appointed": entry.effective_from,
            "ceased_on": entry.ceased_on,
            "active": entry.ceased_on is None,
            "date_of_birth": p.get("date_of_birth"),
            "nationality": p.get("nationality"),
            "occupation": p.get("occupation"),
            "bvn": bvn,
            "document_type": p.get("document_type"),
            "document_number": p.get("document_number"),
            "document_expiry": p.get("document_expiry"),
            "residential_address": p.get("residential_address"),
            "email": p.get("email"),
            "phone": p.get("phone"),
            "other_directorships": p.get("other_directorships", []),
            "shares": (member.particulars or {}).get("shares") if member else None,
            "share_class": (member.particulars or {}).get("class") if member else None,
        })
