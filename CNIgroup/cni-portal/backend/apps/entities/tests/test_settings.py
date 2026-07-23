import pytest

from apps.entities.entity_settings import get_settings, update_settings
from apps.entities.models import Entity


@pytest.mark.django_db
def test_entity_settings_persist_and_scope():
    a = Entity.objects.create(legal_name="Entity A")
    b = Entity.objects.create(legal_name="Entity B")

    update_settings(entity=a, brand_primary_color="#FF0000", retention_days=365)

    a_settings = get_settings(a)
    assert a_settings.brand_primary_color == "#FF0000"   # persisted
    assert a_settings.retention_days == 365

    b_settings = get_settings(b)
    assert b_settings.brand_primary_color == "#2563EB"   # default, scoped separately
