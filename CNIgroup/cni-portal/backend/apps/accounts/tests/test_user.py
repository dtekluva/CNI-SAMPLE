import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

User = get_user_model()


@pytest.mark.django_db
def test_user_email_is_identifier():
    """Given a user created with email, email is the login identifier."""
    user = User.objects.create_user(email="ada@cni.test", password="pw-strong-123")
    assert user.email == "ada@cni.test"
    assert User.USERNAME_FIELD == "email"


@pytest.mark.django_db
def test_duplicate_email_rejected():
    User.objects.create_user(email="dup@cni.test", password="pw-strong-123")
    with pytest.raises(IntegrityError):
        User.objects.create_user(email="dup@cni.test", password="other-pw-456")


@pytest.mark.django_db
def test_superuser_flags():
    su = User.objects.create_superuser(email="root@cni.test", password="pw-strong-123")
    assert su.is_staff and su.is_superuser


def test_user_model_is_swapped(settings):
    """The custom user precedes all FK references (T-A1)."""
    assert settings.AUTH_USER_MODEL == "accounts.User"
    assert get_user_model().__name__ == "User"
