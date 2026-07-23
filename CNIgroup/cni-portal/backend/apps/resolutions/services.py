from django.db.models import Count, Sum
from django.utils import timezone

from apps.audit.models import AuditEvent

from .models import Resolution, Vote


def create_resolution(*, entity, title, text, mover=None, seconder=None, meeting=None,
                      kind=Resolution.Kind.BOARD, voting_mode=Resolution.VotingMode.OPEN,
                      resolution_class=Resolution.ResolutionClass.ORDINARY,
                      amount=None, category="", body="BD", when=None, actor=None):
    when = when or timezone.now()
    year = when.year
    seq = Resolution.objects.filter(entity=entity, year=year).count() + 1
    code = entity.code or "RES"
    number = f"{code}/{body}/{year}/{seq:03d}"
    resolution = Resolution.objects.create(
        entity=entity, meeting=meeting, number=number, year=year, title=title, text=text,
        mover=mover, seconder=seconder, kind=kind, voting_mode=voting_mode,
        resolution_class=resolution_class, amount=amount, category=category,
    )
    AuditEvent.objects.record(action="resolution.created", actor=actor, target=resolution, metadata={"number": number})
    return resolution


def cast_vote(*, resolution, voter, choice, weight=1):
    vote, _ = Vote.objects.update_or_create(
        resolution=resolution, voter=voter, defaults={"choice": choice, "weight": weight}
    )
    return vote


def tally(resolution):
    """Head-count of votes by choice (mode-agnostic)."""
    counts = {c: 0 for c in Vote.Choice.values}
    for row in resolution.votes.values("choice").annotate(n=Count("id")):
        counts[row["choice"]] = row["n"]
    return counts


def weighted_tally(resolution):
    """Weight-sum of votes by choice (poll mode)."""
    counts = {c: 0 for c in Vote.Choice.values}
    for row in resolution.votes.values("choice").annotate(w=Sum("weight")):
        counts[row["choice"]] = row["w"] or 0
    return counts


def results(resolution, *, viewer=None, is_admin=False):
    """
    Mode-aware results view (FR-VOTE-1). A secret ballot records and returns the
    tally but hides who voted how — only a group admin (the cosec running the
    ballot) may see the per-voter breakdown for integrity.
    """
    mode = resolution.voting_mode
    counts = tally(resolution)
    data = {"mode": mode, "tally": counts, "total_votes": sum(counts.values())}
    if resolution.meeting_id:
        from apps.conflicts.services import conflicted_user_ids

        data["recused"] = sorted(conflicted_user_ids(resolution.meeting, resolution.agenda_item))
    if mode == Resolution.VotingMode.POLL:
        data["weighted"] = weighted_tally(resolution)
    reveal = mode != Resolution.VotingMode.SECRET or is_admin
    if reveal:
        data["ballots"] = [
            {"voter": v.voter_id, "choice": v.choice, "weight": v.weight}
            for v in resolution.votes.select_related("voter")
        ]
    else:
        data["ballots"] = None  # secret: individual choices withheld
    return data


def conclude(*, resolution, actor=None):
    from decimal import Decimal

    from .authority import SPECIAL_THRESHOLD

    poll = resolution.voting_mode == Resolution.VotingMode.POLL
    counts = weighted_tally(resolution) if poll else tally(resolution)
    for_, against = counts[Vote.Choice.FOR], counts[Vote.Choice.AGAINST]
    decisive = for_ + against
    if resolution.resolution_class == Resolution.ResolutionClass.SPECIAL:
        # CAMA special resolution: >=75% of the votes cast (for/against)
        passed = decisive > 0 and (Decimal(for_) / Decimal(decisive)) >= SPECIAL_THRESHOLD
    else:
        passed = for_ > against
    resolution.outcome = Resolution.Outcome.PASSED if passed else Resolution.Outcome.FAILED
    resolution.save(update_fields=["outcome"])
    AuditEvent.objects.record(
        action="resolution.concluded", actor=actor, target=resolution,
        metadata={"outcome": resolution.outcome, "mode": resolution.voting_mode,
                  "class": resolution.resolution_class, **counts},
    )
    return resolution
