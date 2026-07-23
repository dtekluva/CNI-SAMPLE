"""
Certified True Copy generation (FR-RES-4). A constant real-world need in Nigeria:
the Company Secretary issues a CTC of a passed/effective resolution for banks/CAC.
"""
from apps.audit.models import AuditEvent

from .models import CertifiedTrueCopy, Resolution


class CTCNotAllowed(Exception):
    pass


def generate_ctc(*, resolution, issued_by, actor=None):
    if resolution.outcome != Resolution.Outcome.PASSED:
        raise CTCNotAllowed("A CTC can only be issued for a passed/effective resolution.")

    count = CertifiedTrueCopy.objects.filter(resolution=resolution).count() + 1
    reference = f"CTC/{resolution.number}/{count:02d}"
    ctc = CertifiedTrueCopy.objects.create(
        resolution=resolution,
        reference=reference,
        body=_render(resolution, issued_by),
        issued_by=issued_by,
    )
    AuditEvent.objects.record(
        action="ctc.issued", actor=actor or issued_by, target=resolution,
        metadata={"reference": reference},
    )
    return ctc


def _render(resolution, issued_by):
    entity = resolution.entity
    signer = getattr(issued_by, "name", "") or issued_by.email
    effective = f"  Effective: {resolution.effective_date}" if resolution.effective_date else ""
    return (
        f"{entity.legal_name}\n"
        f"(RC {entity.cac_rc_number})\n\n"
        f"CERTIFIED TRUE COPY OF RESOLUTION {resolution.number}\n\n"
        f"{resolution.title}\n\n{resolution.text}\n\n"
        f"Outcome: {resolution.get_outcome_display()}{effective}\n\n"
        f"CERTIFIED as a true copy of the resolution duly passed.\n\n"
        f"_____________________________\n"
        f"{signer}\nCompany Secretary"
    )
