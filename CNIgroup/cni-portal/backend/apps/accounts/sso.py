"""
SSO (OIDC) identity mapping — additive (NFR-SEC-1, DECISIONS D-A3).

SSO authenticates existing users via an allow-listed IdP (Google / Microsoft
Entra); it never creates accounts and never bypasses MFA unless the IdP asserts
an MFA-equivalent AMR. Token exchange + ID-token validation happen in the OIDC
callback (deferred until an IdP is configured); this function operates on
already-validated claims and is the single mapping/authorization point.
"""
from django.conf import settings
from django.contrib.auth import get_user_model

from apps.audit.models import AuditEvent


class SSOError(Exception):
    """Raised when an SSO identity cannot be trusted or mapped."""


def map_oidc_identity(claims):
    """Map validated OIDC claims to an active user, or raise SSOError."""
    issuer = claims.get("iss")
    allowed = getattr(settings, "OIDC_ALLOWED_ISSUERS", [])
    if not issuer or issuer not in allowed:
        raise SSOError("Issuer not allow-listed.")

    email = (claims.get("email") or "").strip().lower()
    if not email:
        raise SSOError("No email in claims.")

    User = get_user_model()
    try:
        user = User.objects.get(email__iexact=email, is_active=True)
    except User.DoesNotExist:
        raise SSOError("No matching account.")

    amr = claims.get("amr") or []
    mfa_satisfied = "mfa" in amr or "otp" in amr
    AuditEvent.objects.record(
        action="sso.login",
        actor=user,
        target=user,
        metadata={"iss": issuer, "mfa_satisfied": mfa_satisfied},
    )
    return user
