"""
Global permission-scoped search (FR-RPT-1, checkpoint).

One query across meetings, documents, minutes, resolutions, actions, registers,
committees and announcements. Every stream filters through entities_for_user —
and documents additionally through recusal exclusion — so a result can never
leak something the caller could not open directly.
"""
from django.db.models import Q

from apps.rbac.resolution import entities_for_user, is_group_admin

LIMIT = 5  # per type; the UI links through to the full screens


def global_search(user, q):
    from apps.actions.models import Action
    from apps.announcements.models import Announcement
    from apps.committees.models import Committee
    from apps.conflicts.services import exclude_recused_documents
    from apps.documents.models import Document
    from apps.meetings.models import Meeting
    from apps.registers.models import RegisterEntry
    from apps.resolutions.models import Resolution

    scope = entities_for_user(user)
    results = []

    def add(kind, obj_id, title, subtitle, link):
        results.append({"kind": kind, "id": obj_id, "title": title, "subtitle": subtitle, "link": link})

    for m in Meeting.objects.filter(entity__in=scope, title__icontains=q).select_related("entity")[:LIMIT]:
        add("meeting", m.id, m.title, f"{m.entity.legal_name} · {m.starts_at:%d %b %Y}", f"/meetings/{m.id}")

    docs = Document.objects.filter(entity__in=scope).filter(
        Q(title__icontains=q) | Q(versions__text_content__icontains=q)
    ).distinct()
    if not is_group_admin(user):
        docs = exclude_recused_documents(docs, user)
    for d in docs.select_related("entity")[:LIMIT]:
        add("document", d.id, d.title, f"{d.entity.legal_name} · {d.topic or d.committee or 'General'}", f"/documents/{d.id}")

    for r in Resolution.objects.filter(entity__in=scope).filter(
        Q(title__icontains=q) | Q(number__icontains=q) | Q(text__icontains=q)
    ).select_related("entity")[:LIMIT]:
        add("resolution", r.id, r.title, f"{r.number} · {r.outcome}", "/resolutions")

    for a in Action.objects.filter(entity__in=scope, title__icontains=q).select_related("entity")[:LIMIT]:
        add("action", a.id, a.title, f"{a.entity.legal_name} · {a.status}", "/actions")

    for e in RegisterEntry.objects.filter(entity__in=scope, party_name__icontains=q).select_related("entity")[:LIMIT]:
        add("register", e.id, e.party_name, f"{e.get_register_type_display()} · {e.entity.legal_name}", "/registers")

    for c in Committee.objects.filter(entity__in=scope).filter(
        Q(name__icontains=q) | Q(charter__icontains=q)
    ).select_related("entity")[:LIMIT]:
        add("committee", c.id, c.name, c.entity.legal_name, "/committees")

    for an in Announcement.objects.filter(entity__in=scope).filter(
        Q(title__icontains=q) | Q(body__icontains=q)
    ).select_related("entity")[:LIMIT]:
        add("announcement", an.id, an.title, f"{an.entity.legal_name} · {an.posted_at:%d %b %Y}", "/announcements")

    return results
