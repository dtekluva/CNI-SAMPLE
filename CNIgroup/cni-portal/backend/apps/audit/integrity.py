"""
Record integrity verification (NFR-INT-1, checkpoint).

The statutory record must remain provable after any amount of time and any
personnel change. Two independent proofs:

1. The audit chain — every event links to its predecessor (prev_hash) and its
   own content hash must recompute identically. One altered row breaks the
   chain visibly at that point.
2. Sealed minutes — every SIGNED minutes' stored hash must match a fresh
   recomputation over its blocks, attendees and meeting.
"""
from .models import AuditEvent


def verify_audit_chain():
    prev = ""
    count = 0
    for e in AuditEvent.objects.order_by("id").iterator():
        count += 1
        if e.prev_hash != prev:
            return {"intact": False, "events": count, "break_at": e.id, "reason": "link"}
        if e.compute_hash() != e.hash:
            return {"intact": False, "events": count, "break_at": e.id, "reason": "content"}
        prev = e.hash
    return {"intact": True, "events": count, "break_at": None, "reason": None}


def verify_sealed_minutes():
    from apps.minutes.models import Minutes
    from apps.minutes.services import compute_minutes_hash

    results = []
    for m in Minutes.objects.filter(state=Minutes.State.SIGNED).select_related("meeting", "meeting__entity"):
        results.append({
            "id": m.id,
            "meeting": m.meeting.title,
            "entity": m.meeting.entity.legal_name,
            "intact": bool(m.content_hash) and compute_minutes_hash(m) == m.content_hash,
        })
    return results


def integrity_report():
    chain = verify_audit_chain()
    minutes = verify_sealed_minutes()
    return {
        "audit_chain": chain,
        "sealed_minutes": minutes,
        "all_intact": chain["intact"] and all(m["intact"] for m in minutes),
    }
