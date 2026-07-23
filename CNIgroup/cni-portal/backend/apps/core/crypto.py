"""
Field-level encryption for 'crown jewels' content (NFR-SEC-2).
Symmetric (Fernet) encryption keyed from FIELD_ENCRYPTION_KEY. Used to encrypt
the most sensitive documents at rest, on top of storage-level encryption.
"""
import os

from django.conf import settings


def _key():
    return getattr(settings, "FIELD_ENCRYPTION_KEY", "") or os.getenv("FIELD_ENCRYPTION_KEY", "")


def _fernet():
    from cryptography.fernet import Fernet

    key = _key()
    if not key:
        raise RuntimeError("FIELD_ENCRYPTION_KEY is not configured.")
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt(data: bytes) -> bytes:
    return _fernet().encrypt(data)


def decrypt(token: bytes) -> bytes:
    return _fernet().decrypt(token)
