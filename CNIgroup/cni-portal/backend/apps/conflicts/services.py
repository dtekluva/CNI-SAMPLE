"""Interest & conflict mutations (FR-CONF-1/2) — every write audited."""
from apps.audit.models import AuditEvent

from .models import ConflictDeclaration, InterestDeclaration


def declare_interest(*, actor, entity, director, kind, party, declared_on, details=""):
    interest = InterestDeclaration.objects.create(
        entity=entity, director=director, kind=kind, party=party,
        declared_on=declared_on, details=details,
    )
    AuditEvent.objects.record(
        action="interest.declared", actor=actor, target=interest,
        metadata={"kind": kind, "party": party, "entity": entity.pk},
    )
    return interest


def withdraw_interest(*, actor, interest, on):
    interest.withdrawn_on = on
    interest.save(update_fields=["withdrawn_on"])
    AuditEvent.objects.record(action="interest.withdrawn", actor=actor, target=interest,
                              metadata={"on": str(on)})
    return interest


def declare_conflict(*, actor, meeting, director, agenda_item=None, interest=None, note=""):
    conflict, created = ConflictDeclaration.objects.get_or_create(
        meeting=meeting, agenda_item=agenda_item, director=director,
        defaults={"interest": interest, "note": note},
    )
    if created:
        AuditEvent.objects.record(
            action="conflict.declared", actor=actor, target=conflict,
            metadata={"meeting": meeting.pk, "agenda_item": agenda_item.pk if agenda_item else None},
        )
    return conflict


def exclude_recused_documents(qs, user):
    """
    Item-level recusal overrides inheritance (FR-RBAC-2): a director who has
    declared a conflict loses access to that item's papers — item-level
    declarations hide that agenda item's documents; a whole-meeting declaration
    hides every paper of the meeting. Entity-level access does NOT win here.
    """
    from django.db.models import Q

    return qs.exclude(
        Q(agenda_item__conflict_declarations__director=user)
        | Q(meeting__conflict_declarations__director=user,
            meeting__conflict_declarations__agenda_item__isnull=True)
    )


def conflicted_user_ids(meeting, agenda_item=None):
    """Directors conflicted on an item: item-level plus whole-meeting declarations.
    The hook recusal enforcement (FR-RBAC-2 / FR-VOTE-2) builds on."""
    qs = ConflictDeclaration.objects.filter(meeting=meeting)
    from django.db.models import Q

    qs = qs.filter(Q(agenda_item__isnull=True) | Q(agenda_item=agenda_item)) if agenda_item else qs
    return set(qs.values_list("director_id", flat=True))
