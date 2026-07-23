"""
Delegation of Authority validation (FR-RES-5).

Given a category and amount, the required approver is the lowest tier whose
limit covers the amount. An amount above every tier exceeds delegated authority
and needs a higher power (shareholders / full board sign-off).
"""
from decimal import Decimal

from .models import DelegationRule

SPECIAL_THRESHOLD = Decimal("0.75")


def required_approver(entity, category, amount):
    amount = Decimal(str(amount))
    covering = (
        DelegationRule.objects.filter(entity=entity, category=category, max_amount__gte=amount)
        .order_by("tier")
        .first()
    )
    if covering:
        return {
            "in_authority": True,
            "approver": covering.approver,
            "limit": str(covering.max_amount),
            "tier": covering.tier,
        }
    top = DelegationRule.objects.filter(entity=entity, category=category).order_by("-tier").first()
    return {
        "in_authority": False,
        "approver": "Shareholders — exceeds delegated authority",
        "limit": str(top.max_amount) if top else None,
        "tier": None,
    }


def authority_check(resolution):
    if resolution.amount is None or not resolution.category:
        return {"applicable": False}
    result = required_approver(resolution.entity, resolution.category, resolution.amount)
    result.update({"applicable": True, "amount": str(resolution.amount), "category": resolution.category})
    return result
