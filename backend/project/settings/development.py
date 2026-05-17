"""
Django settings for the DataCube project in the development environment.
"""

import os

from .common import *

# --- Development-Specific Settings ---

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Allow all hosts for local development convenience
# ALLOWED_HOSTS = ['*']

CORS_ORIGIN_ALLOW_ALL = True

# --- Email ---
# OTP / verification: core.infrastructure.resend_client
# With no RESEND_API_KEY, set ALLOW_STDOUT_EMAIL=true to log OTP codes in the terminal.
ALLOW_STDOUT_EMAIL = os.getenv("ALLOW_STDOUT_EMAIL", "true").lower() in ("1", "true", "yes")

# --- CORS ---
# Allow all origins for easy frontend development
CORS_ORIGIN_ALLOW_ALL = True

# --- DRF ---
# Enable the browsable API renderer for development
REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = (
    'rest_framework.renderers.JSONRenderer',
    'rest_framework.renderers.BrowsableAPIRenderer',
)

CELERY_BROKER_URL = 'redis://127.0.0.1:6379/0'
CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'