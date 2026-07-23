import pytest
from django.contrib.auth import get_user_model

from apps.audit.models import AuditEvent
from apps.documents.models import Document, DocumentVersion
from apps.entities.models import Entity
from apps.rbac.models import Role
from apps.rbac.services import assign_role

User = get_user_model()


@pytest.mark.django_db
def test_document_content_and_pdf_reader(mfa_client_factory):
    cosec = User.objects.create_user(email="cosec2@cni.test", password="pw-strong-123")
    assign_role(actor=cosec, user=cosec, role=Role.COMPANY_SECRETARY, entity=None)
    entity = Entity.objects.create(legal_name="Alpha")
    doc = Document.objects.create(entity=entity, title="Budget Paper")
    DocumentVersion.objects.create(document=doc, version_number=1, content_hash="x" * 64,
                                   text_content="SECTION 1\nThe budget is N4.2bn.")
    client = mfa_client_factory(cosec)

    body = client.get(f"/api/documents/{doc.pk}/content/").json()
    assert "N4.2bn" in body["text"] and body["version"] == 1
    assert AuditEvent.objects.filter(action="document.viewed").exists()

    pdf = client.get(f"/api/documents/{doc.pk}/pdf/")
    assert pdf.status_code == 200
    assert pdf["Content-Type"] == "application/pdf"
    assert bytes(pdf.content[:5]) == b"%PDF-"
