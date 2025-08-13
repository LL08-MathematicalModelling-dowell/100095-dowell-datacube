import os
import json
from pathlib import Path
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import timedelta


load_dotenv()

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / 'config.json'

if CONFIG_PATH.exists():
    with open(CONFIG_PATH, encoding='utf-8') as f:
        config = json.load(f)
else:
    config = {}

# Environment flags
# DEBUG = os.getenv('DEBUG', True)
DEBUG=True
SECRET_KEY = os.getenv('SECRET_KEY', config.get('secret_key'))

# MongoDB
MONGODB_URI = os.getenv('MONGODB_URI', config.get('mongo_path'))
MONGODB_DATABASE = os.getenv('MONGODB_DATABASE', config.get('database'))
MONGODB_COLLECTION = os.getenv('MONGODB_COLLECTION', config.get('collection'))

if not all([MONGODB_URI, MONGODB_DATABASE, MONGODB_COLLECTION]):
    raise Exception("MongoDB settings missing. Please set them in config.json or environment.")

MONGODB_CLIENT = MongoClient(MONGODB_URI)
METADATA_DB = MONGODB_CLIENT[MONGODB_DATABASE]
METADATA_COLLECTION = METADATA_DB[MONGODB_COLLECTION]

# SQLite (default for dev)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',') if not DEBUG else [
    '127.0.0.1',
    'localhost',
    'datacube.uxlivinglab.online',
    'www.dowelldatacube.uxlivinglab.online'
]

INSTALLED_APPS = [
    # Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',

    # Third-party
    'corsheaders',
    'rest_framework',

    # Local
    'api',
    'core',
]

SITE_ID = 1
REST_USE_JWT = True

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'api.middleware.UsageMeteringMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'project.urls'
TEMPLATE_DIR = BASE_DIR / 'templates'
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [TEMPLATE_DIR],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'project.wsgi.application'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_HEADERS = ['*']

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
# MY_BASE_URL = os.getenv('MY_BASE_URL', 'https://datacube.uxlivinglab.online')


REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer" if DEBUG else "rest_framework.renderers.JSONRenderer",
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': (
        # We will create this custom JWT auth class in a moment
        'core.utils.authentication.CustomJWTAuthentication',
        'core.utils.authentication.APIKeyAuthentication',    # For service-to-service actions
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'UNAUTHENTICATED_USER': None, # Important for our custom setup
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=7),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=14),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}



EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# In production, you would use something like this:
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = 'smtp.example.com'
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = 'your-email@example.com'
# EMAIL_HOST_PASSWORD = 'your-email-password'
# DEFAULT_FROM_EMAIL = 'noreply@yourdomain.com'




# Logging
# LOGS_DIR = BASE_DIR / 'logs'
# LOGS_DIR.mkdir(parents=True, exist_ok=True)

# LOGGING = {
#     'version': 1,
#     'disable_existing_loggers': False,
#     'formatters': {
#         'verbose': {
#             'format': '{levelname} {asctime} {module} {message}',
#             'style': '{',
#         },
#         'simple': {
#             'format': '{levelname} {message}',
#             'style': '{',
#         },
#     },
#     'handlers': {
#         'console': {
#             'level': 'DEBUG' if DEBUG else 'INFO',
#             'class': 'logging.StreamHandler',
#             'formatter': 'simple',
#         },
#         'file': {
#             'level': 'INFO',
#             'class': 'logging.FileHandler',
#             'filename': LOGS_DIR / 'application.log',
#             'formatter': 'verbose',
#         },
#     },
#     'loggers': {
#         'django': {
#             'handlers': ['console', 'file'],
#             'level': 'DEBUG' if DEBUG else 'INFO',
#             'propagate': True,
#         },
#     },
# }
