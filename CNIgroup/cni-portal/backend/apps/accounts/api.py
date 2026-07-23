from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth import login as dj_login
from django.contrib.auth import logout as dj_logout
from django.middleware.csrf import get_token
from django_otp import login as otp_login
from django_otp.plugins.otp_totp.models import TOTPDevice
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.audit.models import AuditEvent

from .permissions import IsMFAVerified
from .services import enroll_totp, record_mfa_verified


@api_view(["GET"])
@permission_classes([AllowAny])
def csrf(request):
    """Prime the CSRF cookie for the SPA."""
    return Response({"csrfToken": get_token(request)})


@api_view(["GET"])
@permission_classes([AllowAny])
def session(request):
    """Auth + MFA state without requiring MFA (used by the app to route)."""
    u = request.user
    if not u.is_authenticated:
        return Response({"authenticated": False})
    verify = getattr(u, "is_verified", None)
    return Response({
        "authenticated": True,
        "mfa_verified": bool(callable(verify) and verify()),
        "mfa_enrolled": TOTPDevice.objects.devices_for_user(u, confirmed=True).exists(),
        "email": u.email,
        "name": u.name,
    })


@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    user = authenticate(request, username=request.data.get("email"), password=request.data.get("password"))
    if user is None:
        return Response({"detail": "Invalid credentials."}, status=401)
    dj_login(request, user)
    AuditEvent.objects.record(action="auth.login", actor=user, target=user)
    return Response({"email": user.email, "mfa_required": True})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    AuditEvent.objects.record(action="auth.logout", actor=request.user, target=request.user)
    dj_logout(request)
    return Response({"ok": True})


@api_view(["GET"])
@permission_classes([IsMFAVerified])
def me(request):
    """Current user — the canonical MFA-protected endpoint."""
    u = request.user
    return Response({"email": u.email, "name": u.name})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mfa_enroll(request):
    """
    Start (or resume) TOTP enrolment; returns a provisioning URL for the QR code.

    Idempotent: a reload must not change the secret out from under a user who
    already scanned it, and an already-enrolled user must never be handed a fresh
    secret. If a confirmed device exists we report enrolment complete; otherwise
    we reuse the pending device (pruning any duplicates left by earlier reloads)
    or create the first one.
    """
    if TOTPDevice.objects.devices_for_user(request.user, confirmed=True).exists():
        return Response({"enrolled": True}, status=200)
    pending = list(TOTPDevice.objects.devices_for_user(request.user, confirmed=False))
    if pending:
        device, *duplicates = pending
        for extra in duplicates:
            extra.delete()
    else:
        device = enroll_totp(request.user, confirmed=False)
    return Response({"config_url": device.config_url, "enrolled": False}, status=201)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mfa_verify(request):
    """Confirm a TOTP token, mark the session MFA-verified, audit it."""
    token = str(request.data.get("token", ""))
    # Prefer a confirmed device (returning user); fall back to the pending one (enrolling).
    device = (
        TOTPDevice.objects.devices_for_user(request.user, confirmed=True).first()
        or TOTPDevice.objects.devices_for_user(request.user, confirmed=False).first()
    )
    if device is None:
        return Response({"detail": "Invalid token."}, status=400)
    # DEMO bypass (settings.MFA_ACCEPT_ANY_CODE): accept any non-empty code.
    accept_any = getattr(settings, "MFA_ACCEPT_ANY_CODE", False)
    if not (accept_any and token) and not device.verify_token(token):
        return Response({"detail": "Invalid token."}, status=400)
    if not device.confirmed:
        device.confirmed = True
        device.save()
    otp_login(request._request, device)
    record_mfa_verified(request.user)
    return Response({"status": "verified"})
