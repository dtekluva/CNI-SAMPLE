"""
Register mutations (FR-ENT-3). Every write is audited so the chain of custody
of a statutory record is provable. Entries are ceased, never deleted.
"""
from apps.audit.models import AuditEvent

from .models import RegisterEntry


def add_entry(*, actor, entity, register_type, party_name, effective_from, particulars=None, notes=""):
    entry = RegisterEntry.objects.create(
        entity=entity,
        register_type=register_type,
        party_name=party_name,
        effective_from=effective_from,
        particulars=particulars or {},
        notes=notes,
    )
    AuditEvent.objects.record(
        action="register.entry.added",
        actor=actor,
        target=entry,
        metadata={"register": register_type, "entity": entity.pk},
    )
    return entry


def cease_entry(*, actor, entry, on):
    """Close a register entry (party left) without destroying the historical record."""
    entry.ceased_on = on
    entry.save(update_fields=["ceased_on", "updated_at"])
    AuditEvent.objects.record(
        action="register.entry.ceased",
        actor=actor,
        target=entry,
        metadata={"ceased_on": str(on)},
    )
    return entry


def entries_as_at(queryset, on_date):
    """Filter a register queryset to the parties on the register at a past date (CAMA proof)."""
    from django.db.models import Q

    return queryset.filter(effective_from__lte=on_date).filter(
        Q(ceased_on__isnull=True) | Q(ceased_on__gt=on_date)
    )
