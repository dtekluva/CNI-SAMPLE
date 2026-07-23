import time

from django.conf import settings
from django.contrib.auth import logout


class InactivityTimeoutMiddleware:
    """
    Enforce an idle session timeout (NFR-SEC-1). If the authenticated user has
    been inactive beyond SESSION_INACTIVITY_TIMEOUT seconds, flush the session.
    Runs after AuthenticationMiddleware / OTPMiddleware.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        timeout = getattr(settings, "SESSION_INACTIVITY_TIMEOUT", 1800)
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated:
            now = int(time.time())
            last = request.session.get("last_activity")
            if last is not None and now - last > timeout:
                logout(request)  # flushes the session
            else:
                request.session["last_activity"] = now
        return self.get_response(request)
