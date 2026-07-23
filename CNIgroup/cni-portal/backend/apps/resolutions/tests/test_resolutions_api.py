import pytest
from django.contrib.auth import get_user_model

from apps.entities.models import Entity
from apps.rbac.models import Role
from apps.rbac.services import assign_role
from apps.resolutions.services import create_resolution

User = get_user_model()


def _cosec_on(entity, mfa_client_factory, email="cosec@cni.test"):
    u = User.objects.create_user(email=email, password="pw-strong-123")
    assign_role(actor=u, user=u, role=Role.COMPANY_SECRETARY, entity=entity)
    return u, mfa_client_factory(u)


@pytest.mark.django_db
def test_resolutions_scoped(mfa_client_factory):
    a = Entity.objects.create(legal_name="Entity A", code="A")
    b = Entity.objects.create(legal_name="Entity B", code="B")
    create_resolution(entity=a, title="RA", text="x")
    create_resolution(entity=b, title="RB", text="x")
    _, client = _cosec_on(a, mfa_client_factory)
    titles = [r["title"] for r in client.get("/api/resolutions/").json()]
    assert titles == ["RA"]


@pytest.mark.django_db
def test_vote_and_conclude_api(mfa_client_factory):
    entity = Entity.objects.create(legal_name="CNI Pay", code="CNI")
    _, client = _cosec_on(entity, mfa_client_factory)
    res = client.post("/api/resolutions/", {"entity": entity.id, "title": "Approve", "text": "x"}, format="json").json()
    client.post(f"/api/resolutions/{res['id']}/vote/", {"choice": "for"}, format="json")
    concluded = client.post(f"/api/resolutions/{res['id']}/conclude/").json()
    assert concluded["outcome"] == "passed"


@pytest.mark.django_db
def test_sign_and_ctc_api(mfa_client_factory):
    entity = Entity.objects.create(legal_name="CNI Pay", code="CNI", cac_rc_number="RC1")
    _, client = _cosec_on(entity, mfa_client_factory)
    res = client.post("/api/resolutions/", {"entity": entity.id, "title": "Open account", "text": "x"}, format="json").json()
    client.post(f"/api/resolutions/{res['id']}/circulate/", {"threshold": 1}, format="json")
    signed = client.post(f"/api/resolutions/{res['id']}/sign/").json()
    assert signed["outcome"] == "passed"
    ctc = client.post(f"/api/resolutions/{res['id']}/ctc/")
    assert ctc.status_code == 201 and "reference" in ctc.json()
