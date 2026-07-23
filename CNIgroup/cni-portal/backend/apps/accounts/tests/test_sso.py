import pytest
from django.contrib.auth import get_user_model

from apps.accounts.sso import SSOError, map_oidc_identity
from apps.audit.models import AuditEvent

User = get_user_model()
ISS = "https://accounts.google.com"


@pytest.mark.django_db
def test_oidc_maps_to_existing_user(settings):
    settings.OIDC_ALLOWED_ISSUERS = [ISS]
    user = User.objects.create_user(email="sso@cni.test", password="pw-strong-123")
    mapped = map_oidc_identity({"iss": ISS, "email": "SSO@cni.test", "amr": ["mfa"]})
    assert mapped == user
    assert AuditEvent.objects.filter(action="sso.login", actor=user).exists()


@pytest.mark.django_db
def test_oidc_rejects_unknown_identity(settings):
    settings.OIDC_ALLOWED_ISSUERS = [ISS]
    with pytest.raises(SSOError):
        map_oidc_identity({"iss": ISS, "email": "ghost@cni.test"})


@pytest.mark.django_db
def test_oidc_rejects_unlisted_issuer(settings):
    settings.OIDC_ALLOWED_ISSUERS = [ISS]
    User.objects.create_user(email="x@cni.test", password="pw-strong-123")
    with pytest.raises(SSOError):
        map_oidc_identity({"iss": "https://evil.example", "email": "x@cni.test"})
