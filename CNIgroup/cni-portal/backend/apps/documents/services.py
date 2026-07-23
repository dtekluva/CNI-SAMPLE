import hashlib

from django.db.models import Q

from apps.rbac.resolution import entities_for_user

from .models import Document, DocumentVersion


def add_version(*, document, data: bytes, uploaded_by=None, storage_key="", text_content=""):
    """Store a new version; prior versions are retained and each carries a hash."""
    latest = document.versions.first()  # highest version (ordering: -version_number)
    next_number = (latest.version_number + 1) if latest else 1
    return DocumentVersion.objects.create(
        document=document,
        version_number=next_number,
        content_hash=hashlib.sha256(data).hexdigest(),
        storage_key=storage_key,
        text_content=text_content,
        uploaded_by=uploaded_by,
    )


def search_documents(*, user, query):
    """Permission-scoped full-text search across title and extracted text."""
    entities = entities_for_user(user)
    return (
        Document.objects.filter(entity__in=entities)
        .filter(Q(title__icontains=query) | Q(versions__text_content__icontains=query))
        .distinct()
    )
