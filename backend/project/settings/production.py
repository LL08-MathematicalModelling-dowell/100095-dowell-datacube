"""
Django settings for the DataCube project in the production environment.
"""
from ast import If
import os
from .common import *


# SECURITY WARNING: keep the secret key used in production secret!
# The SECRET_KEY is already loaded from .env in common.py
if not SECRET_KEY:
    raise ValueError("No SECRET_KEY set for production environment.")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# ----------------- CORS Allowed Hosts -----------------
# Allow all origins for CORS for /api/ endpoints, but restrict others
CORS_ORIGIN_ALLOW_ALL = False
# CORS_ORIGIN_WHITELIST is set from environment variable in common.py, 
# and CORS_URLS_REGEX restricts it to /api/ endpoints only, so we 
#   can allow all origins for API while keeping other endpoints secure. 
# This allows the frontend to connect to the API from any domain, while preventing CORS issues for non-API endpoints.
CORS_ORIGIN_WHITELIST = os.getenv('ALLOWED_HOSTS', '').split(',')
if not CORS_ORIGIN_WHITELIST:
    raise ValueError("No ALLOWED_HOSTS set for production environment, which is required for CORS_ORIGIN_WHITELIST.")

CORS_URLS_REGEX = r'^/api/.*$'

# --- Security ---
CSRF_COOKIE_SECURE = True
# SESSION_COOKIE_SECURE = True
# SECURE_SSL_REDIRECT = True
# SECURE_HSTS_SECONDS = 31536000  # 1 year
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# SECURE_HSTS_PRELOAD = True

# --- Email ---
# Use a real SMTP backend for production
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = os.getenv('EMAIL_HOST')
# EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
# EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
# EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
# EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
# DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER)

# --- DRF ---
# Disable the browsable API renderer in production
REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = (
    'rest_framework.renderers.JSONRenderer',
)

# --- Logging ---
# Configure robust logging for production
# LOGGING = {
#     'version': 1,
#     'disable_existing_loggers': False,
#     'formatters': {
#         'verbose': {
#             'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
#             'style': '{',
#         },
#     },
#     'handlers': {
#         'console': {
#             'level': 'INFO',
#             'class': 'logging.StreamHandler',
#             'formatter': 'verbose',
#         },
#     },
#     'root': {
#         'handlers': ['console'],
#         'level': 'INFO',
#     },
#     'loggers': {
#         'django': {
#             'handlers': ['console'],
#             'level': 'INFO',
#             'propagate': False,
#         },
#     },
# }



CELERY_BROKER_URL = 'redis://redis:6379/0'
CELERY_RESULT_BACKEND = 'redis://redis:6379/0'


# CELERY_BROKER_URL = 'redis://127.0.0.1:6379/0'
# CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379/0'

CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'