"""
Minutes approval workflow (FR-MIN-2): Draft -> Chairman review -> Circulated ->
Adopted -> Signed. Each transition is logged; adoption is blocked while any
comment is undispositioned.
"""
from apps.audit.models import AuditEvent

from .models import MinuteComment, Minutes

ALLOWED = {
    Minutes.State.DRAFT: {Minutes.State.CHAIRMAN_REVIEW},
    Minutes.State.CHAIRMAN_REVIEW: {Minutes.State.CIRCULATED, Minutes.State.DRAFT},
    Minutes.State.CIRCULATED: {Minutes.State.ADOPTED, Minutes.State.CHAIRMAN_REVIEW},
    Minutes.State.ADOPTED: {Minutes.State.SIGNED},
    Minutes.State.SIGNED: set(),
}


class TransitionError(Exception):
    pass


class UndispositionedComments(Exception):
    pass


def transition(*, actor, minutes, to_state):
    current = minutes.state
    if to_state not in ALLOWED.get(current, set()):
        raise TransitionError(f"Cannot move minutes from {current} to {to_state}.")
    if to_state == Minutes.State.ADOPTED and minutes.comments.filter(dispositioned=False).exists():
        raise UndispositionedComments("All comments must be dispositioned before adoption.")
    minutes.state = to_state
    minutes.save(update_fields=["state", "updated_at"])
    if to_state == Minutes.State.SIGNED:
        from .services import seal_signed

        seal_signed(minutes=minutes, actor=actor)
        AuditEvent.objects.record(
            action="minutes.signed", actor=actor, target=minutes,
            metadata={"content_hash": minutes.content_hash},
        )
    AuditEvent.objects.record(
        action="minutes.state_changed",
        actor=actor,
        target=minutes,
        metadata={"from": current, "to": to_state},
    )
    return minutes


def add_comment(*, minutes, author, text):
    return MinuteComment.objects.create(minutes=minutes, author=author, text=text)


def dispose_comment(*, comment):
    comment.dispositioned = True
    comment.save(update_fields=["dispositioned"])
    return comment
