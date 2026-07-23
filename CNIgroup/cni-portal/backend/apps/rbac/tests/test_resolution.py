import pytest
from django.contrib.auth import get_user_model

from apps.entities.models import Entity
from apps.rbac.models import Role
from apps.rbac.resolution import entities_for_user, has_entity_access, has_role
from apps.rbac.services import assign_role

User = get_user_model()


@pytest.mark.django_db
def test_no_cross_entity_leak():
    user = User.objects.create_user(email="ned@cni.test", password="pw-strong-123")
    a = Entity.objects.create(legal_name="Entity A")
    b = Entity.objects.create(legal_name="Entity B")
    assign_role(actor=user, user=user, role=Role.NON_EXECUTIVE_DIRECTOR, entity=a)

    assert has_entity_access(user, a) is True
    assert has_entity_access(user, b) is False


@pytest.mark.django_db
def test_group_role_sees_scoped_consolidation():
    user = User.objects.create_user(email="chair@cni.test", password="pw-strong-123")
    holdco = Entity.objects.create(legal_name="Holdco")
    sub = Entity.objects.create(legal_name="Sub", parent=holdco)
    other = Entity.objects.create(legal_name="Other")
    assign_role(actor=user, user=user, role=Role.CHAIRMAN, entity=holdco)

    ents = set(entities_for_user(user))
    assert holdco in ents and sub in ents
    assert other not in ents  # only the remit


@pytest.mark.django_db
def test_default_deny():
    user = User.objects.create_user(email="nobody@cni.test", password="pw-strong-123")
    e = Entity.objects.create(legal_name="Entity E")
    assert has_entity_access(user, e) is False
    assert has_role(user, e, Role.CHAIRMAN) is False
