import hashlib

import pytest
from django.contrib.auth import get_user_model

from apps.documents.models import Document
from apps.documents.services import add_version, search_documents
from apps.entities.models import Entity
from apps.rbac.models import Role
from apps.rbac.services import assign_role

User = get_user_model()


@pytest.mark.django_db
def test_new_version_retains_prior_and_hashes():
    entity = Entity.objects.create(legal_name="CNI Pay")
    doc = Document.objects.create(entity=entity, title="Q3 Accounts")

    v1 = add_version(document=doc, data=b"first")
    v2 = add_version(document=doc, data=b"second")

    assert (v1.version_number, v2.version_number) == (1, 2)
    assert doc.versions.count() == 2                       # prior retained
    assert v1.content_hash == hashlib.sha256(b"first").hexdigest()
    assert v1.content_hash != v2.content_hash


@pytest.mark.django_db
def test_search_is_permission_scoped():
    a = Entity.objects.create(legal_name="Entity A")
    b = Entity.objects.create(legal_name="Entity B")
    Document.objects.create(entity=a, title="Alpha Secret")
    Document.objects.create(entity=b, title="Beta Secret")

    user = User.objects.create_user(email="ned@cni.test", password="pw-strong-123")
    assign_role(actor=user, user=user, role=Role.NON_EXECUTIVE_DIRECTOR, entity=a)

    titles = [d.title for d in search_documents(user=user, query="Secret")]
    assert "Alpha Secret" in titles
    assert "Beta Secret" not in titles  # no cross-entity leak
