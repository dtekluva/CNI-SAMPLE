from apps.audit.models import AuditEvent

from .models import EntitySettings


def get_settings(entity):
    settings, _ = EntitySettings.objects.get_or_create(entity=entity)
    return settings


def update_settings(*, entity, actor=None, **fields):
    settings = get_settings(entity)
    for key, value in fields.items():
        setattr(settings, key, value)
    settings.save()
    AuditEvent.objects.record(
        action="entity.settings_updated", actor=actor, target=entity,
        metadata={"fields": list(fields.keys())},
    )
    return settings
