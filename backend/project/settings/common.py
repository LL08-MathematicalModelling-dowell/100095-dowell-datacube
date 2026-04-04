"""
Django settings for the DataCube project that are common to all environments.
"""
import os
from pathlib import Path
from datetime import timedelta
from pymongo import AsyncMongoClient # type: ignore
# from celery.schedules import crontab
from dotenv import load_dotenv # type: ignore


load_dotenv()

# --- Core Paths and Config Loading ---
BASE_DIR = Path(__file__).resolve().parent.parent.parent


DATACUBE_FREE_TIER_MB = 500

# Paths
# CONFIG_PATH = BASE_DIR / 'config.json'

# if CONFIG_PATH.exists():
#     with open(CONFIG_PATH, encoding='utf-8') as f:
#         config = json.load(f)
# else:
#     config = {}

# --- Security ---
# SECRET_KEY will be set in development.py and production.py
SECRET_KEY = os.getenv('SECRET_KEY', 'SECRET_KEY_DUMMY')

# --- Application Definition ---
INSTALLED_APPS = [
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
    'rest_framework_simplejwt',
    # Local Apps
    'api',
    'core',
    'analytics',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # For serving static files in production
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'api.middleware.UsageMeteringMiddleware',
    'analytics.middleware.DatacubeObservabilityMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'project.urls'
WSGI_APPLICATION = 'project.wsgi.application'
SITE_ID = 1

# --- Templates ---
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

# --- Database ---
# We keep the default as SQLite. Production will override this.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# MongoDB
MONGODB_URI = os.getenv('MONGODB_URI')
MONGODB_DATABASE = os.getenv('MONGODB_DATABASE')
MONGODB_COLLECTION = os.getenv('MONGODB_COLLECTION')
DATACUBE_V2_AUTH_DB = os.getenv("AUTH_DB_NAME")
FILE_STORAGE_DB_NAME = os.getenv("FILE_STORAGE_DB_NAME")


if not all([MONGODB_URI, MONGODB_DATABASE, MONGODB_COLLECTION, DATACUBE_V2_AUTH_DB, FILE_STORAGE_DB_NAME]):
    raise ValueError("MongoDB settings missing. Please set them in environment.")

MONGODB_CLIENT = AsyncMongoClient(MONGODB_URI)
METADATA_DB = MONGODB_CLIENT[MONGODB_DATABASE] # type: ignore
METADATA_COLLECTION = METADATA_DB[MONGODB_COLLECTION] # type: ignore
FILE_METADATA_COLLECTION = METADATA_DB["file_metadata"]


# --- Password Validation ---
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# --- Internationalization ---
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True

USE_TZ = True

# --- Static Files ---
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# --- Default Primary Key Field Type ---
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- DRF and JWT Settings ---
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'core.utils.authentication.CustomJWTAuthentication',
        'core.utils.authentication.APIKeyAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'UNAUTHENTICATED_USER': None,
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=7),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=14),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
}



# CELERY_BEAT_SCHEDULE = {
#     "prune-inactive-fields-daily": {
#         "task": "api.tasks.run_pruning_for_all_databases",
#         "schedule": crontab(hour=3, minute=0),  # 3 AM daily
#         "args": (False,)  # Set dry_run=False in production
#     },
# }