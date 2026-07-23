import pytest
from django.contrib.auth import get_user_model

from apps.audit.models import AuditEvent
from apps.entities.models import Entity
from apps.rbac.breakglass import invoke_break_glass
from apps.rbac.resolution import can_access_content, has_entity_access

User = get_user_model()


@pytest.mark.django_db
def test_admin_denied_by_default():
    admin = User.objects.create_user(email="itadmin@cni.test", password="pw-strong-123", is_staff=True)
    entity = Entity.objects.create(legal_name="Entity A")
    # No content role -> denied.
    assert has_entity_access(admin, entity) is False
    assert can_access_content(admin, entity) is False


@pytest.mark.django_db
def test_break_glass_requires_reason():
    admin = User.objects.create_user(email="itadmin@cni.test", password="pw-strong-123")
    entity = Entity.objects.create(legal_name="Entity A")
    with pytest.raises(ValueError):
        invoke_break_glass(actor=admin, entity=entity, reason="  ")


@pytest.mark.django_db
def test_break_glass_grants_access_and_audits():
    admin = User.objects.create_user(email="itadmin@cni.test", password="pw-strong-123")
    entity = Entity.objects.create(legal_name="Entity A")

    grant = invoke_break_glass(actor=admin, entity=entity, reason="prod incident #42", ttl_minutes=30)
    assert grant.is_active()
    assert can_access_content(admin, entity) is True

    ev = AuditEvent.objects.filter(action="break_glass.invoked", actor=admin).first()
    assert ev is not None and ev.metadata.get("severity") == "high"
    assert AuditEvent.objects.filter(action="break_glass.cosec_notified").exists()


@pytest.mark.django_db
def test_expired_break_glass_denies():
    admin = User.objects.create_user(email="itadmin@cni.test", password="pw-strong-123")
    entity = Entity.objects.create(legal_name="Entity A")
    grant = invoke_break_glass(actor=admin, entity=entity, reason="incident", ttl_minutes=30)
    # Force expiry.
    from django.utils import timezone
    from datetime import timedelta
    grant.expires_at = timezone.now() - timedelta(minutes=1)
    grant.save()
    assert can_access_content(admin, entity) is False
