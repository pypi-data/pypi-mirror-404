from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

REQUIRED_SETTINGS = [
    "GOTENBERG_URL",
]

OPTIONAL_SETTINGS = [
    "GOTENBERG_API_TIMEOUT",
]

def get_config():
    try:
        return settings.GOTENBERG_CONFIG
    except AttributeError:
        raise ImproperlyConfigured(
            "GOTENBERG_CONFIG setting is required"
        )
        
def validate_settings():
    config = get_config()

    for key in REQUIRED_SETTINGS:
        if key not in config:
            raise ImproperlyConfigured(
                f"GOTENBERG_CONFIG['{key}'] is required"
            )