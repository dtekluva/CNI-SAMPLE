import pytest
from django.contrib.auth import get_user_model

from apps.actions.services import create_action
from apps.entities.models import Entity
from apps.rbac.models import Role
from apps.rbac.services import assign_role

User = get_user_model()


def _cosec_on(entity, mfa_client_factory):
    u = User.objects.create_user(email="cosec@cni.test", password="pw-strong-123")
    assign_role(actor=u, user=u, role=Role.COMPANY_SECRETARY, entity=entity)
    return u, mfa_client_factory(u)


@pytest.mark.django_db
def test_actions_scoped(mfa_client_factory):
    a = Entity.objects.create(legal_name="Entity A")
    b = Entity.objects.create(legal_name="Entity B")
    create_action(entity=a, title="Task A")
    create_action(entity=b, title="Task B")
    _, client = _cosec_on(a, mfa_client_factory)
    titles = [x["title"] for x in client.get("/api/actions/").json()]
    assert titles == ["Task A"]


@pytest.mark.django_db
def test_complete_action_api(mfa_client_factory):
    entity = Entity.objects.create(legal_name="CNI Pay")
    _, client = _cosec_on(entity, mfa_client_factory)
    a = create_action(entity=entity, title="Follow up")
    resp = client.post(f"/api/actions/{a.id}/complete/", {"evidence": "done, see email"}, format="json")
    assert resp.status_code == 200
    assert resp.json()["status"] == "done"
    assert resp.json()["evidence"] == "done, see email"


@pytest.mark.django_db
def test_reminders_escalation_and_overdue_dashboard(mfa_client_factory):
    from datetime import timedelta
    from django.utils import timezone
    from django.contrib.auth import get_user_model
    from apps.actions.models import Action
    from apps.entities.models import Entity
    from apps.notifications.models import Notification
    from apps.rbac.models import Role
    from apps.rbac.services import assign_role

    User = get_user_model()
    cosec = User.objects.create_user(email="cosec-rem@cni.test", password="pw-strong-123")
    assign_role(actor=cosec, user=cosec, role=Role.COMPANY_SECRETARY, entity=None)
    entity = Entity.objects.create(legal_name="Alpha")
    owner = User.objects.create_user(email="owner-rem@cni.test", password="pw-strong-123", name="Owner")
    assign_role(actor=cosec, user=owner, role=Role.NON_EXECUTIVE_DIRECTOR, entity=entity)
    today = timezone.now().date()

    Action.objects.create(entity=entity, title="Due soon", owner=owner, status=Action.Status.OPEN, due_date=today + timedelta(days=3))
    Action.objects.create(entity=entity, title="Overdue thing", owner=owner, status=Action.Status.OPEN, due_date=today - timedelta(days=10))

    res = mfa_client_factory(cosec).post("/api/actions/run-reminders/", {}, format="json").json()
    assert res["reminded"] == 1 and res["escalated"] >= 1
    assert Notification.objects.filter(recipient=owner, event_type="action.due_soon").exists()
    assert Notification.objects.filter(recipient=cosec, event_type="action.escalated").exists()

    dash = mfa_client_factory(cosec).get("/api/actions/overdue-dashboard/").json()
    alpha = next(g for g in dash if g["entity_name"] == "Alpha")
    overdue = next(i for i in alpha["items"] if i["title"] == "Overdue thing")
    assert overdue["overdue_days"] == 10 and overdue["owner"] == "Owner"
