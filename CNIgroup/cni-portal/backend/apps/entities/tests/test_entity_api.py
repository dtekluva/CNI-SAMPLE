import pytest
from django.contrib.auth import get_user_model
from django_otp.plugins.otp_totp.models import TOTPDevice
from rest_framework.test import APIClient

from apps.audit.models import AuditEvent
from apps.entities.models import Entity
from apps.rbac.models import Role
from apps.rbac.services import assign_role

User = get_user_model()


def mfa_client(user):
    """An APIClient with an MFA-verified session."""
    device = TOTPDevice.objects.create(user=user, name="d", confirmed=True)
    client = APIClient()
    client.force_login(user)
    session = client.session
    session["otp_device_id"] = device.persistent_id
    session.save()
    return client


@pytest.mark.django_db
def test_entity_create_requires_group_admin_and_audits():
    cosec = User.objects.create_user(email="cosec@cni.test", password="pw-strong-123")
    assign_role(actor=cosec, user=cosec, role=Role.COMPANY_SECRETARY, entity=None)
    client = mfa_client(cosec)

    resp = client.post("/api/entities/", {"legal_name": "CNI Holdings"}, format="json")
    assert resp.status_code == 201
    assert AuditEvent.objects.filter(action="entity.created").exists()


@pytest.mark.django_db
def test_entity_list_is_scoped():
    cosec = User.objects.create_user(email="cosec@cni.test", password="pw-strong-123")
    assign_role(actor=cosec, user=cosec, role=Role.COMPANY_SECRETARY, entity=None)
    a = Entity.objects.create(legal_name="Alpha")
    b = Entity.objects.create(legal_name="Beta")

    director = User.objects.create_user(email="dir@cni.test", password="pw-strong-123")
    assign_role(actor=cosec, user=director, role=Role.NON_EXECUTIVE_DIRECTOR, entity=a)

    names = [e["legal_name"] for e in mfa_client(director).get("/api/entities/").json()]
    assert names == ["Alpha"]  # only their entity, no leak of Beta

    all_names = {e["legal_name"] for e in mfa_client(cosec).get("/api/entities/").json()}
    assert {"Alpha", "Beta"} <= all_names  # group role sees all


@pytest.mark.django_db
def test_entity_create_denied_for_non_group_admin():
    director = User.objects.create_user(email="dir@cni.test", password="pw-strong-123")
    a = Entity.objects.create(legal_name="Alpha")
    assign_role(actor=director, user=director, role=Role.NON_EXECUTIVE_DIRECTOR, entity=a)
    resp = mfa_client(director).post("/api/entities/", {"legal_name": "Sneaky"}, format="json")
    assert resp.status_code == 403
