from django.conf import settings
from django.core.checks import Error, register

INSECURE_DEFAULT = "dev-insecure-change-me"


@register()
def secret_key_not_default(app_configs, **kwargs):
    """Fail deploy checks if the insecure dev SECRET_KEY leaks into a real env."""
    errors = []
    if not settings.DEBUG and settings.SECRET_KEY == INSECURE_DEFAULT:
        errors.append(
            Error(
                "SECRET_KEY is the insecure development default in a non-DEBUG environment.",
                id="core.E001",
                hint="Set DJANGO_SECRET_KEY in the environment.",
            )
        )
    return errors
