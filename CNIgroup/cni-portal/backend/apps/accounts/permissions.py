from rest_framework.permissions import BasePermission


class IsMFAVerified(BasePermission):
    """
    Authenticated AND multi-factor verified (NFR-SEC-1).

    django-otp's OTPMiddleware adds `is_verified()` to the request user based on
    the OTP device confirmed in the session. Protected endpoints require it.
    """

    message = "Multi-factor authentication is required."

    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        if not (user and user.is_authenticated):
            return False
        verify = getattr(user, "is_verified", None)
        return bool(callable(verify) and verify())
