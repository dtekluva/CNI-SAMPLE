import pytest
from django_otp.plugins.otp_totp.models import TOTPDevice
from rest_framework.test import APIClient


@pytest.fixture
def mfa_client_factory(db):
    """Return an APIClient with an MFA-verified session for a given user."""

    def make(user):
        device = TOTPDevice.objects.create(user=user, name="d", confirmed=True)
        client = APIClient()
        client.force_login(user)
        session = client.session
        session["otp_device_id"] = device.persistent_id
        session.save()
        return client

    return make
