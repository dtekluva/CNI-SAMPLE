import pytest
from django.contrib.auth import get_user_model

from apps.audit.integrity import integrity_report, verify_audit_chain
from apps.audit.models import AuditEvent
from apps.entities.models import Entity
from apps.rbac.models import Role
from apps.rbac.services import assign_role

User = get_user_model()


@pytest.mark.django_db
def test_audit_chain_verifies_and_detects_tampering():
    u = User.objects.create_user(email="a@cni.test", password="pw-strong-123")
    for i in range(5):
        AuditEvent.objects.record(action=f"demo.event.{i}", actor=u)

    assert verify_audit_chain()["intact"] is True

    # tamper with a middle row via update() (bypasses the append-only save guard)
    victim = AuditEvent.objects.order_by("id")[2]
    AuditEvent.objects.filter(pk=victim.pk).update(metadata={"forged": True})
    broken = verify_audit_chain()
    assert broken["intact"] is False
    assert broken["break_at"] == victim.pk
    assert broken["reason"] == "content"


@pytest.mark.django_db
def test_integrity_endpoint_admin_only(mfa_client_factory):
    cosec = User.objects.create_user(email="cosec-int@cni.test", password="pw-strong-123")
    assign_role(actor=cosec, user=cosec, role=Role.COMPANY_SECRETARY, entity=None)
    entity = Entity.objects.create(legal_name="Alpha")
    director = User.objects.create_user(email="dir-int@cni.test", password="pw-strong-123")
    assign_role(actor=cosec, user=director, role=Role.NON_EXECUTIVE_DIRECTOR, entity=entity)

    assert mfa_client_factory(director).get("/api/integrity/").status_code == 403

    report = mfa_client_factory(cosec).get("/api/integrity/").json()
    assert report["audit_chain"]["intact"] is True
    assert "sealed_minutes" in report and "all_intact" in report
    assert AuditEvent.objects.filter(action="integrity.verified").exists()


@pytest.mark.django_db
def test_report_covers_sealed_minutes():
    report = integrity_report()
    assert report["audit_chain"]["intact"] is True
    assert report["sealed_minutes"] == []
    assert report["all_intact"] is True
