"""
Django settings for the DataCube project in the development environment.
"""
from .common import *

# --- Development-Specific Settings ---

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Allow all hosts for local development convenience
ALLOWED_HOSTS = ['*']

# --- Email ---
# Use the console backend to see emails printed in the terminal
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# --- CORS ---
# Allow all origins for easy frontend development
CORS_ORIGIN_ALLOW_ALL = True

# --- DRF ---
# Enable the browsable API renderer for development
REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = (
    'rest_framework.renderers.JSONRenderer',
    'rest_framework.renderers.BrowsableAPIRenderer',
)