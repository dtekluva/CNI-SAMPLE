import inspect

import pytest

from apps.core.checks import secret_key_not_default
from apps.core.storages import select_storage


def test_settings_reads_secret_from_env():
    import config.settings as s

    src = inspect.getsource(s)
    assert 'os.getenv("DJANGO_SECRET_KEY"' in src  # no hard-coded secret


def test_secret_key_check_flags_default(settings):
    settings.DEBUG = False
    settings.SECRET_KEY = "dev-insecure-change-me"
    errors = secret_key_not_default(None)
    assert any(e.id == "core.E001" for e in errors)


def test_secret_key_check_passes_with_real_key(settings):
    settings.DEBUG = False
    settings.SECRET_KEY = "a-real-secret-value-xyz-123"
    assert secret_key_not_default(None) == []


def test_residency_flag_routes_storage(settings):
    settings.DATA_RESIDENCY = "NG"
    assert select_storage()["region"] == "af-south-1"
    assert select_storage("EU")["region"] == "eu-west-1"


def test_field_encryption_roundtrip(settings):
    from cryptography.fernet import Fernet

    settings.FIELD_ENCRYPTION_KEY = Fernet.generate_key().decode()
    from apps.core.crypto import decrypt, encrypt

    ct = encrypt(b"confidential board paper")
    assert ct != b"confidential board paper"
    assert decrypt(ct) == b"confidential board paper"
