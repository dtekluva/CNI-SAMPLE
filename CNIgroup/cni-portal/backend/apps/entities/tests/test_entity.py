from datetime import date

import pytest
from django.core.exceptions import ValidationError

from apps.entities.models import Entity


@pytest.mark.django_db
def test_entity_tree():
    holdco = Entity.objects.create(legal_name="CNI Holdings")
    sub = Entity.objects.create(legal_name="CNI Pay", parent=holdco)
    assert sub.parent == holdco
    assert list(holdco.children.all()) == [sub]
    assert sub.ancestors() == [holdco]


@pytest.mark.django_db
def test_cycle_rejected():
    a = Entity.objects.create(legal_name="A")
    b = Entity.objects.create(legal_name="B", parent=a)
    a.parent = b
    with pytest.raises(ValidationError):
        a.save()


@pytest.mark.django_db
def test_incomplete_flag():
    partial = Entity.objects.create(legal_name="Partial Co")
    assert partial.is_complete is False

    full = Entity.objects.create(
        legal_name="Full Co",
        cac_rc_number="RC123456",
        incorporation_date=date(2020, 1, 1),
        registered_address="12 Marina, Lagos",
        financial_year_end="12-31",
    )
    assert full.is_complete is True
