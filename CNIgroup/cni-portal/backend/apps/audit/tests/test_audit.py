import pytest
from django.contrib.auth import get_user_model

from apps.audit.models import AuditEvent, verify_chain

User = get_user_model()


@pytest.mark.django_db
def test_event_records_actor_action_target():
    user = User.objects.create_user(email="cosec@cni.test", password="pw-strong-123")
    event = AuditEvent.objects.record(action="user.created", actor=user, target=user)
    assert event.actor == user
    assert event.action == "user.created"
    assert event.target == user
    assert event.timestamp is not None
    assert event.hash  # non-empty


@pytest.mark.django_db
def test_event_is_append_only():
    event = AuditEvent.objects.record(action="test.event")
    with pytest.raises(ValueError):
        event.save()  # update forbidden
    with pytest.raises(ValueError):
        event.delete()  # delete forbidden


@pytest.mark.django_db
def test_hash_chain_detects_tampering():
    for i in range(3):
        AuditEvent.objects.record(action=f"event.{i}")
    assert verify_chain() is True

    # Tamper a past row directly, bypassing the model guard (bulk update).
    first = AuditEvent.objects.order_by("id").first()
    AuditEvent.objects.filter(pk=first.pk).update(action="tampered")

    assert verify_chain() is False


@pytest.mark.django_db
def test_chain_links_prev_hash():
    a = AuditEvent.objects.record(action="a")
    b = AuditEvent.objects.record(action="b")
    assert a.prev_hash == ""
    assert b.prev_hash == a.hash
