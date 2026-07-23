import pytest


@pytest.mark.django_db
def test_voting_modes_open_secret_poll(mfa_client_factory):
    from django.contrib.auth import get_user_model
    from apps.entities.models import Entity
    from apps.rbac.models import Role
    from apps.rbac.services import assign_role
    from apps.resolutions.models import Resolution

    User = get_user_model()
    cosec = User.objects.create_user(email="cosec-vm@cni.test", password="pw-strong-123")
    assign_role(actor=cosec, user=cosec, role=Role.COMPANY_SECRETARY, entity=None)
    entity = Entity.objects.create(legal_name="Alpha", code="AL")
    director = User.objects.create_user(email="dir-vm@cni.test", password="pw-strong-123")
    assign_role(actor=cosec, user=director, role=Role.NON_EXECUTIVE_DIRECTOR, entity=entity)
    admin_c = mfa_client_factory(cosec)
    dir_c = mfa_client_factory(director)

    # SECRET ballot: votes recorded, but a director cannot see who voted how
    secret = admin_c.post("/api/resolutions/", {
        "entity": entity.pk, "title": "Secret motion", "text": "THAT ...", "voting_mode": "secret",
    }, format="json").json()
    dir_view = dir_c.post(f"/api/resolutions/{secret['id']}/vote/", {"choice": "for"}, format="json").json()
    assert dir_view["mode"] == "secret"
    assert dir_view["tally"]["for"] == 1        # tally is recorded
    assert dir_view["ballots"] is None           # but individual choices are hidden
    admin_view = admin_c.get(f"/api/resolutions/{secret['id']}/results/").json()
    assert admin_view["ballots"] is not None      # cosec sees the breakdown for integrity

    # POLL: weighted by shares; a small head-count can be outweighed
    poll = admin_c.post("/api/resolutions/", {
        "entity": entity.pk, "title": "Weighted motion", "text": "THAT ...", "voting_mode": "poll",
    }, format="json").json()
    admin_c.post(f"/api/resolutions/{poll['id']}/vote/", {"choice": "against", "weight": 100}, format="json")
    dir_c.post(f"/api/resolutions/{poll['id']}/vote/", {"choice": "for", "weight": 5}, format="json")
    concl = admin_c.post(f"/api/resolutions/{poll['id']}/conclude/", format="json").json()
    assert concl["outcome"] == "failed"           # 100 against outweighs 5 for, though 1-1 by head


@pytest.mark.django_db
def test_conflicted_director_is_recused_from_voting(mfa_client_factory):
    from django.contrib.auth import get_user_model
    from django.utils import timezone
    from apps.entities.models import Entity
    from apps.meetings.models import AgendaItem, Meeting
    from apps.rbac.models import Role
    from apps.rbac.services import assign_role
    from apps.resolutions.models import Resolution
    from apps.audit.models import AuditEvent

    User = get_user_model()
    cosec = User.objects.create_user(email="cosec-rv@cni.test", password="pw-strong-123")
    assign_role(actor=cosec, user=cosec, role=Role.COMPANY_SECRETARY, entity=None)
    entity = Entity.objects.create(legal_name="Alpha", code="AL")
    director = User.objects.create_user(email="dir-rv@cni.test", password="pw-strong-123")
    assign_role(actor=cosec, user=director, role=Role.NON_EXECUTIVE_DIRECTOR, entity=entity)
    meeting = Meeting.objects.create(entity=entity, title="Q3", starts_at=timezone.now())
    item = AgendaItem.objects.create(meeting=meeting, title="Sable award", position=1)
    res = Resolution.objects.create(entity=entity, meeting=meeting, agenda_item=item, number="AL/BD/2026/050",
                                    year=2026, title="Award Sable", text="THAT ...")
    dir_c = mfa_client_factory(director)

    # can vote before declaring a conflict
    assert dir_c.post(f"/api/resolutions/{res.pk}/vote/", {"choice": "for"}, format="json").status_code == 200

    # declare a conflict on this item -> recused from the vote
    dir_c.post("/api/conflicts/", {"meeting": meeting.pk, "agenda_item": item.pk}, format="json")
    blocked = dir_c.post(f"/api/resolutions/{res.pk}/vote/", {"choice": "for"}, format="json")
    assert blocked.status_code == 409
    assert AuditEvent.objects.filter(action="resolution.vote_blocked_recusal").exists()

    results = mfa_client_factory(cosec).get(f"/api/resolutions/{res.pk}/results/").json()
    assert director.pk in results["recused"]  # exclusion is surfaced on the record


@pytest.mark.django_db
def test_special_resolution_needs_75_percent():
    from django.contrib.auth import get_user_model
    from apps.entities.models import Entity
    from apps.resolutions.models import Resolution, Vote
    from apps.resolutions.services import cast_vote, conclude

    User = get_user_model()
    entity = Entity.objects.create(legal_name="Alpha", code="AL")

    def voters(n):
        return [User.objects.create_user(email=f"v{i}-{Resolution.objects.count()}@x.test", password="pw-strong-123") for i in range(n)]

    # SPECIAL: 3 for / 1 against = 75% -> passes
    special = Resolution.objects.create(entity=entity, number="AL/BD/2026/900", year=2026, title="Alter articles",
                                        text="THAT ...", resolution_class=Resolution.ResolutionClass.SPECIAL)
    vs = voters(4)
    for v in vs[:3]:
        cast_vote(resolution=special, voter=v, choice=Vote.Choice.FOR)
    cast_vote(resolution=special, voter=vs[3], choice=Vote.Choice.AGAINST)
    conclude(resolution=special)
    special.refresh_from_db()
    assert special.outcome == "passed"

    # SPECIAL: 2 for / 1 against = 66.7% -> fails (would pass as ordinary)
    special2 = Resolution.objects.create(entity=entity, number="AL/BD/2026/901", year=2026, title="Reduce capital",
                                         text="THAT ...", resolution_class=Resolution.ResolutionClass.SPECIAL)
    vs2 = voters(3)
    for v in vs2[:2]:
        cast_vote(resolution=special2, voter=v, choice=Vote.Choice.FOR)
    cast_vote(resolution=special2, voter=vs2[2], choice=Vote.Choice.AGAINST)
    conclude(resolution=special2)
    special2.refresh_from_db()
    assert special2.outcome == "failed"  # simple majority isn't enough for a special resolution


@pytest.mark.django_db
def test_doa_matrix_and_authority_check(mfa_client_factory):
    from decimal import Decimal
    from django.contrib.auth import get_user_model
    from apps.entities.models import Entity
    from apps.rbac.models import Role
    from apps.rbac.services import assign_role
    from apps.resolutions.models import DelegationRule, Resolution

    User = get_user_model()
    cosec = User.objects.create_user(email="cosec-doa@cni.test", password="pw-strong-123")
    assign_role(actor=cosec, user=cosec, role=Role.COMPANY_SECRETARY, entity=None)
    entity = Entity.objects.create(legal_name="Alpha", code="AL")
    director = User.objects.create_user(email="dir-doa@cni.test", password="pw-strong-123")
    assign_role(actor=cosec, user=director, role=Role.NON_EXECUTIVE_DIRECTOR, entity=entity)
    client = mfa_client_factory(cosec)

    # cosec builds a 3-tier capex matrix
    for tier, (who, limit) in enumerate([("Managing Director", "50000000"), ("Board Risk Committee", "200000000"), ("Full Board", "1000000000")], start=1):
        r = client.post("/api/doa/", {"entity": entity.pk, "category": "Capital expenditure", "approver": who, "max_amount": limit, "tier": tier}, format="json")
        assert r.status_code == 201
    # directors can read but not write
    assert mfa_client_factory(director).post("/api/doa/", {"entity": entity.pk, "category": "x", "approver": "y", "max_amount": "1", "tier": 9}, format="json").status_code == 403
    assert len(mfa_client_factory(director).get("/api/doa/").json()) == 3

    # a N120m capex resolution -> required approver is the Board Risk Committee (tier 2)
    within = Resolution.objects.create(entity=entity, number="AL/BD/2026/950", year=2026, title="Buy switch",
                                       text="...", amount=Decimal("120000000"), category="Capital expenditure")
    chk = client.get(f"/api/resolutions/{within.pk}/authority/").json()
    assert chk["applicable"] and chk["in_authority"] and chk["approver"] == "Board Risk Committee"

    # a N2bn capex resolution exceeds every tier -> out of authority
    over = Resolution.objects.create(entity=entity, number="AL/BD/2026/951", year=2026, title="Mega capex",
                                     text="...", amount=Decimal("2000000000"), category="Capital expenditure")
    chk2 = client.get(f"/api/resolutions/{over.pk}/authority/").json()
    assert chk2["in_authority"] is False and "exceeds" in chk2["approver"].lower()
