from django_otp.plugins.otp_totp.models import TOTPDevice

from apps.audit.models import AuditEvent


def enroll_totp(user, *, confirmed=True, name="default"):
    """Create a TOTP device for the user and audit the enrolment."""
    device = TOTPDevice.objects.create(user=user, name=name, confirmed=confirmed)
    AuditEvent.objects.record(
        action="mfa.enrolled", actor=user, target=user, metadata={"device": name}
    )
    return device


def record_mfa_verified(user):
    """Audit a successful MFA verification."""
    AuditEvent.objects.record(action="mfa.verified", actor=user, target=user)
