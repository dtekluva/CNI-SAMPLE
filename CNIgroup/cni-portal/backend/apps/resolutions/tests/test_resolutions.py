from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from django.contrib.auth import get_user_model

from apps.entities.models import Entity
from apps.resolutions.models import Vote
from apps.resolutions.services import cast_vote, conclude, create_resolution, tally

User = get_user_model()
UTC = ZoneInfo("UTC")
WHEN = datetime(2026, 7, 1, 10, 0, tzinfo=UTC)


@pytest.mark.django_db
def test_resolution_records_votes_and_outcome():
    entity = Entity.objects.create(legal_name="CNI Pay", code="CNI")
    u1 = User.objects.create_user(email="d1@cni.test", password="pw-strong-123")
    u2 = User.objects.create_user(email="d2@cni.test", password="pw-strong-123")
    u3 = User.objects.create_user(email="d3@cni.test", password="pw-strong-123")

    r = create_resolution(entity=entity, title="Approve accounts", text="...", mover=u1, seconder=u2, when=WHEN)
    cast_vote(resolution=r, voter=u1, choice=Vote.Choice.FOR)
    cast_vote(resolution=r, voter=u2, choice=Vote.Choice.FOR)
    cast_vote(resolution=r, voter=u3, choice=Vote.Choice.AGAINST)

    counts = tally(r)
    assert counts["for"] == 2 and counts["against"] == 1

    conclude(resolution=r)
    r.refresh_from_db()
    assert r.outcome == "passed"


@pytest.mark.django_db
def test_auto_numbering_sequences_per_entity():
    a = Entity.objects.create(legal_name="CNI Pay", code="CNI")
    b = Entity.objects.create(legal_name="Other Co", code="OTH")

    r1 = create_resolution(entity=a, title="R1", text="x", when=WHEN)
    r2 = create_resolution(entity=a, title="R2", text="x", when=WHEN)
    rb = create_resolution(entity=b, title="RB", text="x", when=WHEN)

    assert r1.number == "CNI/BD/2026/001"
    assert r2.number == "CNI/BD/2026/002"
    assert rb.number == "OTH/BD/2026/001"  # separate sequence per entity
