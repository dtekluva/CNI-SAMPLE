import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory

from apps.entities.models import Entity
from apps.rbac.breakglass import invoke_break_glass
from apps.rbac.permissions import CanAccessContent

User = get_user_model()


@pytest.mark.django_db
def test_platform_admin_cannot_read_content_silently():
    # A full Django superuser with NO governance role.
    admin = User.objects.create_superuser(email="root@cni.test", password="pw-strong-123")
    entity = Entity.objects.create(legal_name="Entity A")

    perm = CanAccessContent()
    request = APIRequestFactory().get("/")
    request.user = admin

    # Superuser status does not grant content access.
    assert perm.has_object_permission(request, None, entity) is False

    # Break-glass is the only admin path in — and it's logged.
    invoke_break_glass(actor=admin, entity=entity, reason="prod incident")
    assert perm.has_object_permission(request, None, entity) is True
