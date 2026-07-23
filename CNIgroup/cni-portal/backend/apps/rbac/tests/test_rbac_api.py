import pytest
from django.contrib.auth import get_user_model

from apps.audit.models import AuditEvent
from apps.entities.models import Entity
from apps.rbac.models import Role, RoleAssignment
from apps.rbac.services import assign_role

User = get_user_model()


@pytest.fixture
def cosec(db):
    u = User.objects.create_user(email="cosec@cni.test", password="pw-strong-123", name="Cosec")
    assign_role(actor=u, user=u, role=Role.COMPANY_SECRETARY, entity=None)
    return u


@pytest.mark.django_db
def test_admin_assigns_and_revokes_role_audited(cosec, mfa_client_factory):
    entity = Entity.objects.create(legal_name="Alpha")
    director = User.objects.create_user(email="dir@cni.test", password="pw-strong-123", name="Ada")
    client = mfa_client_factory(cosec)

    resp = client.post(
        "/api/roles/",
        {"user": director.pk, "role": Role.NON_EXECUTIVE_DIRECTOR, "entity": entity.pk},
        format="json",
    )
    assert resp.status_code == 201
    assert resp.json()["scope"] == "Alpha"
    assert AuditEvent.objects.filter(action="role.assigned").exists()

    aid = resp.json()["id"]
    assert client.delete(f"/api/roles/{aid}/").status_code == 204
    assert not RoleAssignment.objects.filter(pk=aid).exists()
    assert AuditEvent.objects.filter(action="role.revoked").exists()


@pytest.mark.django_db
def test_non_admin_sees_only_own_and_cannot_assign(cosec, mfa_client_factory):
    entity = Entity.objects.create(legal_name="Alpha")
    director = User.objects.create_user(email="dir@cni.test", password="pw-strong-123")
    assign_role(actor=cosec, user=director, role=Role.NON_EXECUTIVE_DIRECTOR, entity=entity)
    other = User.objects.create_user(email="other@cni.test", password="pw-strong-123")
    assign_role(actor=cosec, user=other, role=Role.NON_EXECUTIVE_DIRECTOR, entity=entity)

    rows = mfa_client_factory(director).get("/api/roles/").json()
    assert {r["user"] for r in rows} == {director.pk}  # only own assignments

    denied = mfa_client_factory(director).post(
        "/api/roles/", {"user": other.pk, "role": Role.CHAIRMAN, "entity": entity.pk}, format="json"
    )
    assert denied.status_code == 403
    assert mfa_client_factory(director).get("/api/roles/options/").json()["can_manage"] is False


@pytest.mark.django_db
def test_admin_options_lists_roles_users_entities(cosec, mfa_client_factory):
    Entity.objects.create(legal_name="Alpha")
    opts = mfa_client_factory(cosec).get("/api/roles/options/").json()
    assert opts["can_manage"] is True
    assert any(r["value"] == "chairman" for r in opts["roles"])
    assert any(e["legal_name"] == "Alpha" for e in opts["entities"])
    assert any(u["email"] == "cosec@cni.test" for u in opts["users"])
