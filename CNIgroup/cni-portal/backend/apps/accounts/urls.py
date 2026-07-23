from django.urls import path

from . import api

urlpatterns = [
    path("me/", api.me, name="me"),
    path("auth/csrf/", api.csrf, name="csrf"),
    path("auth/session/", api.session, name="session"),
    path("auth/login/", api.login_view, name="login"),
    path("auth/logout/", api.logout_view, name="logout"),
    path("auth/mfa/enroll/", api.mfa_enroll, name="mfa-enroll"),
    path("auth/mfa/verify/", api.mfa_verify, name="mfa-verify"),
]
