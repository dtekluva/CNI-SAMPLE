from apps.audit.models import AuditEvent

from .models import Action


def create_action(*, entity, title, owner=None, owner_name="", due_date=None,
                  meeting=None, agenda_item=None, actor=None):
    action = Action.objects.create(
        entity=entity, title=title, owner=owner, owner_name=owner_name,
        due_date=due_date, meeting=meeting, agenda_item=agenda_item,
    )
    AuditEvent.objects.record(action="action.created", actor=actor, target=action)
    return action


def complete_action(*, action, evidence="", actor=None):
    action.status = Action.Status.DONE
    action.evidence = evidence
    action.save(update_fields=["status", "evidence"])
    AuditEvent.objects.record(action="action.completed", actor=actor, target=action)
    return action
