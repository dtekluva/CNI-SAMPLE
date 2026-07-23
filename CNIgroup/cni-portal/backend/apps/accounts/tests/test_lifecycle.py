import pytest
from django.contrib.auth import get_user_model

from apps.accounts.lifecycle import bulk_import_users, offboard_user, onboard_user
from apps.audit.models import AuditEvent
from apps.entities.models import Entity
from apps.rbac.models import Role, RoleAssignment
from apps.rbac.resolution import can_access_content
from apps.rbac.services import assign_role

User = get_user_model()


@pytest.mark.django_db
def test_onboard_creates_and_audits():
    actor = User.objects.create_user(email="cosec@cni.test", password="pw-strong-123")
    user = onboard_user(actor=actor, email="new@cni.test", name="New Director")
    assert user.email == "new@cni.test"
    assert AuditEvent.objects.filter(action="user.onboarded").exists()


@pytest.mark.django_db
def test_offboard_revokes_but_preserves_history():
    actor = User.objects.create_user(email="cosec@cni.test", password="pw-strong-123")
    subject = User.objects.create_user(email="dir@cni.test", password="pw-strong-123")
    entity = Entity.objects.create(legal_name="Entity A")
    assign_role(actor=actor, user=subject, role=Role.NON_EXECUTIVE_DIRECTOR, entity=entity)

    # An action attributed to the subject before they leave.
    prior = AuditEvent.objects.record(action="minutes.signed", actor=subject, target=entity)

    offboard_user(actor=actor, user=subject)

    subject.refresh_from_db()
    assert subject.is_active is False                          # deactivated
    assert not RoleAssignment.objects.filter(user=subject).exists()  # access revoked
    assert can_access_content(subject, entity) is False

    prior.refresh_from_db()
    assert prior.actor_id == subject.pk                        # attribution intact
    assert AuditEvent.objects.filter(action="user.offboarded").exists()


@pytest.mark.django_db
def test_bulk_import():
    actor = User.objects.create_user(email="cosec@cni.test", password="pw-strong-123")
    created = bulk_import_users(
        actor=actor,
        rows=[{"email": "a@cni.test", "name": "A"}, {"email": "b@cni.test", "name": "B"}],
    )
    assert len(created) == 2
    assert User.objects.filter(email__in=["a@cni.test", "b@cni.test"]).count() == 2
