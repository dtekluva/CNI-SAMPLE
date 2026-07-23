import pytest
from django.contrib.auth import get_user_model

from apps.audit.models import AuditEvent
from apps.rbac.models import Role
from apps.rbac.services import assign_role

User = get_user_model()


@pytest.mark.django_db
def test_audit_api_scoped_readonly(mfa_client_factory):
    admin = User.objects.create_user(email="admin@cni.test", password="pw-strong-123")
    assign_role(actor=admin, user=admin, role=Role.SUPER_ADMIN, entity=None)  # group-level
    regular = User.objects.create_user(email="reg@cni.test", password="pw-strong-123")

    AuditEvent.objects.record(action="x.happened", actor=regular)
    AuditEvent.objects.record(action="y.happened", actor=admin)

    admin_client = mfa_client_factory(admin)
    all_actions = {e["action"] for e in admin_client.get("/api/audit/").json()}
    assert "x.happened" in all_actions and "y.happened" in all_actions  # admin sees all

    reg_actions = {e["action"] for e in mfa_client_factory(regular).get("/api/audit/").json()}
    assert "x.happened" in reg_actions and "y.happened" not in reg_actions  # own trail only

    assert admin_client.post("/api/audit/", {}, format="json").status_code == 405  # read-only


@pytest.mark.django_db
def test_audit_filter(mfa_client_factory):
    admin = User.objects.create_user(email="admin@cni.test", password="pw-strong-123")
    assign_role(actor=admin, user=admin, role=Role.SUPER_ADMIN, entity=None)
    AuditEvent.objects.record(action="alpha", actor=admin)
    AuditEvent.objects.record(action="beta", actor=admin)

    data = mfa_client_factory(admin).get("/api/audit/?action=alpha").json()
    assert {e["action"] for e in data} == {"alpha"}
