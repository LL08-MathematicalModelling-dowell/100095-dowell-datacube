"""
Django settings for the DataCube project in the production environment.
"""
import os

from .common import *


if not SECRET_KEY or SECRET_KEY == "SECRET_KEY_DUMMY":
    raise ValueError(
        "Production requires a strong SECRET_KEY env var (do not use SECRET_KEY_DUMMY)."
    )

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['datacube.uxlivinglab.online', 'localhost', '127.0.0.1', 'backend']

# ----------------- CORS Allowed Hosts -----------------
CORS_ALLOW_ALL_ORIGINS = True  # This makes the API "public" to any domain
CORS_URLS_REGEX = r'^/api/.*$' # Only apply these open rules to /api/ routes

# --- Security ---
CSRF_COOKIE_SECURE = True
# SESSION_COOKIE_SECURE = True
# SECURE_SSL_REDIRECT = True
# SECURE_HSTS_SECONDS = 31536000  # 1 year
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# SECURE_HSTS_PRELOAD = True

# --- Email ---
# OTP / verification: Resend only (core.infrastructure.resend_client).

# --- DRF ---
# Disable the browsable API renderer in production
REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = (
    'rest_framework.renderers.JSONRenderer',
)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "datacube": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}



CELERY_BROKER_URL = 'redis://redis:6379/0'
CELERY_RESULT_BACKEND = 'redis://redis:6379/0'


# CELERY_BROKER_URL = 'redis://127.0.0.1:6379/0'
# CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379/0'

CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'