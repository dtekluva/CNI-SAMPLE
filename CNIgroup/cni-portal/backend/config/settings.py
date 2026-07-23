"""
Django settings — CNI Group Governance Portal API.
Security-first baseline (see PRD §17 / DECISIONS D-A3). Values are env-driven.
"""
from pathlib import Path
import os

import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env_bool(key: str, default: str = "false") -> bool:
    return os.getenv(key, default).strip().lower() in ("1", "true", "yes", "on")


SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-insecure-change-me")
DEBUG = env_bool("DJANGO_DEBUG", "true")

# DEMO ONLY — when true, MFA verification accepts any non-empty code (skips the
# TOTP check) so the preview is easy to walk. Defaults OFF; enable per-env in .env.
# Must be turned off before any real/production use.
MFA_ACCEPT_ANY_CODE = env_bool("MFA_ACCEPT_ANY_CODE", "false")
ALLOWED_HOSTS = [h for h in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # third-party
    "rest_framework",
    "corsheaders",
    "django_otp",
    "django_otp.plugins.otp_totp",
    # local
    "apps.accounts",
    "apps.audit",
    "apps.entities",
    "apps.registers",
    "apps.conflicts",
    "apps.committees",
    "apps.compliance",
    "apps.announcements",
    "apps.rbac",
    "apps.meetings",
    "apps.documents",
    "apps.minutes",
    "apps.resolutions",
    "apps.actions",
    "apps.notifications",
    "apps.core",
]

# Email-based identity from day one (T-A1) so all FKs reference the custom user.
AUTH_USER_MODEL = "accounts.User"

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django_otp.middleware.OTPMiddleware",  # MFA (NFR-SEC-1)
    "apps.accounts.middleware.InactivityTimeoutMiddleware",  # idle session timeout
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# Idle session timeout in seconds (NFR-SEC-1).
SESSION_INACTIVITY_TIMEOUT = int(os.getenv("SESSION_INACTIVITY_TIMEOUT", "1800"))

# SSO / OIDC (NFR-SEC-1, additive). Token exchange wired once an IdP is configured.
OIDC_ALLOWED_ISSUERS = [i for i in os.getenv("OIDC_ALLOWED_ISSUERS", "").split(",") if i]
OIDC_CLIENT_ID = os.getenv("OIDC_CLIENT_ID", "")
OIDC_CLIENT_SECRET = os.getenv("OIDC_CLIENT_SECRET", "")
OIDC_DISCOVERY_URL = os.getenv("OIDC_DISCOVERY_URL", "")

# Encryption & data residency (NFR-SEC-2, NFR-SEC-3, D-B3).
FIELD_ENCRYPTION_KEY = os.getenv("FIELD_ENCRYPTION_KEY", "")
DATA_RESIDENCY = os.getenv("DATA_RESIDENCY", "default")
DATA_RESIDENCY_STORAGES = {
    "default": {"backend": "local", "bucket": os.getenv("STORAGE_BUCKET", "cni-default")},
    "NG": {"backend": "s3", "region": "af-south-1", "bucket": os.getenv("STORAGE_BUCKET_NG", "cni-ng")},
    "EU": {"backend": "s3", "region": "eu-west-1", "bucket": os.getenv("STORAGE_BUCKET_EU", "cni-eu")},
}

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# DB — Postgres in dev/prod (DATABASE_URL); SQLite fallback for fast unit tests (DECISIONS D-A2).
DATABASES = {
    "default": dj_database_url.parse(
        os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'db.sqlite3'}"),
        conn_max_age=600,
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    # Least-privilege default: endpoints are authenticated unless explicitly opened (PRD P2).
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

CORS_ALLOWED_ORIGINS = [
    o for o in os.getenv(
        "CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",") if o
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Lagos"  # Nigerian group (PRD §0)
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Behind a TLS-terminating reverse proxy (nginx).
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
CSRF_TRUSTED_ORIGINS = [o for o in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",") if o]

# Hardening that only applies when DEBUG is off (dev stays convenient).
if not DEBUG:
    SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", "true")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = int(os.getenv("DJANGO_HSTS_SECONDS", "3600"))
    SECURE_CONTENT_TYPE_NOSNIFF = True
