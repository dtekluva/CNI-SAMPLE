import pytest
from django.contrib.auth import get_user_model

from apps.audit.models import AuditEvent
from apps.entities.models import Entity
from apps.rbac.models import Role, RoleAssignment
from apps.rbac.services import assign_role, revoke_role

User = get_user_model()


@pytest.mark.django_db
def test_role_scoped_to_entity():
    actor = User.objects.create_user(email="cosec@cni.test", password="pw-strong-123")
    a = Entity.objects.create(legal_name="Entity A")
    b = Entity.objects.create(legal_name="Entity B")
    assign_role(actor=actor, user=actor, role=Role.NON_EXECUTIVE_DIRECTOR, entity=a)

    assert RoleAssignment.objects.for_user_entity(actor, a).exists()
    assert not RoleAssignment.objects.for_user_entity(actor, b).exists()


@pytest.mark.django_db
def test_group_level_role_matches_all_entities():
    actor = User.objects.create_user(email="chair@cni.test", password="pw-strong-123")
    a = Entity.objects.create(legal_name="Entity A")
    assign_role(actor=actor, user=actor, role=Role.CHAIRMAN, entity=None)
    assert RoleAssignment.objects.for_user_entity(actor, a).exists()


@pytest.mark.django_db
def test_role_change_audited():
    actor = User.objects.create_user(email="admin@cni.test", password="pw-strong-123")
    subject = User.objects.create_user(email="dir@cni.test", password="pw-strong-123")
    entity = Entity.objects.create(legal_name="Entity E")

    ra = assign_role(actor=actor, user=subject, role=Role.NON_EXECUTIVE_DIRECTOR, entity=entity)
    assert AuditEvent.objects.filter(action="role.assigned").exists()

    revoke_role(actor=actor, assignment=ra)
    assert AuditEvent.objects.filter(action="role.revoked").exists()
    assert not RoleAssignment.objects.filter(pk=ra.pk).exists()
