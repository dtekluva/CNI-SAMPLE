"""
Circular (written) resolutions + e-signature (FR-RES-2).

Draft -> circulate -> per-director e-sign -> effective once the signature
threshold is met; lapses if it expires first. E-signing is behind a provider
interface, stubbed until an e-sign vendor is selected (DECISIONS D-B4). Live
provider calls stay human-gated (NFR-AI/D-D4 posture); every signature is audited.
"""
from django.utils import timezone

from apps.audit.models import AuditEvent

from .models import Resolution, Signature


class ResolutionLapsed(Exception):
    pass


class SignatureProvider:
    def sign(self, *, resolution, signer) -> str:
        raise NotImplementedError


class StubSignatureProvider(SignatureProvider):
    """Placeholder until DocuSign/Adobe is wired (D-B4)."""

    def sign(self, *, resolution, signer):
        return f"stub-cert:{resolution.number}:{signer.pk}"


def get_provider():
    return StubSignatureProvider()


def circulate(*, resolution, threshold, expires_at, actor=None):
    resolution.kind = Resolution.Kind.CIRCULAR
    resolution.threshold = threshold
    resolution.expires_at = expires_at
    resolution.save(update_fields=["kind", "threshold", "expires_at"])
    AuditEvent.objects.record(
        action="resolution.circulated", actor=actor, target=resolution, metadata={"threshold": threshold}
    )
    return resolution


def sign(*, resolution, signer, when=None):
    when = when or timezone.now()
    if (
        resolution.expires_at
        and when > resolution.expires_at
        and resolution.outcome != Resolution.Outcome.PASSED
    ):
        _lapse(resolution)
        raise ResolutionLapsed("This circular resolution has lapsed.")

    certificate = get_provider().sign(resolution=resolution, signer=signer)
    signature, _ = Signature.objects.get_or_create(
        resolution=resolution, signer=signer, defaults={"certificate": certificate}
    )
    AuditEvent.objects.record(
        action="resolution.signed", actor=signer, target=resolution,
        metadata={"certificate": signature.certificate},
    )
    _check_effectiveness(resolution, when)
    return signature


def _check_effectiveness(resolution, when):
    if resolution.threshold > 0 and resolution.signatures.count() >= resolution.threshold:
        if resolution.outcome != Resolution.Outcome.PASSED:
            resolution.outcome = Resolution.Outcome.PASSED
            resolution.effective_date = when.date()
            resolution.save(update_fields=["outcome", "effective_date"])
            AuditEvent.objects.record(action="resolution.effective", actor=None, target=resolution)


def _lapse(resolution):
    if resolution.outcome != Resolution.Outcome.PASSED:
        resolution.outcome = Resolution.Outcome.LAPSED
        resolution.save(update_fields=["outcome"])


def lapse_if_expired(*, resolution, as_of):
    if (
        resolution.outcome != Resolution.Outcome.PASSED
        and resolution.expires_at
        and as_of > resolution.expires_at
    ):
        _lapse(resolution)
    return resolution
