"""
Django settings for the DataCube project that are common to all environments.
"""
import os
import json
from pathlib import Path
from datetime import timedelta
from pymongo import MongoClient
from dotenv import load_dotenv

# --- Core Paths and Config Loading ---
BASE_DIR = Path(__file__).resolve().parent.parent.parent

load_dotenv(os.path.join(BASE_DIR, '.env'))


# Paths
CONFIG_PATH = BASE_DIR / 'config.json'

if CONFIG_PATH.exists():
    with open(CONFIG_PATH, encoding='utf-8') as f:
        config = json.load(f)
else:
    config = {}

# --- Security ---
# SECRET_KEY will be set in development.py and production.py
SECRET_KEY = os.getenv('SECRET_KEY_DUMMY', os.getenv('SECRET_KEY'))

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
    'rest_framework_simplejwt.token_blacklist', # For token rotation
    # Local Apps
    'api',
    'core',
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
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
#     }
# }

# --- MongoDB Connection (Centralized and Cleaned) ---
# Moved client instantiation out of settings to avoid global state issues.
# It's better to instantiate the client where it's needed (e.g., in a db.py file)
# MONGODB_URI = os.getenv('MONGODB_URI')
# MONGODB_DATABASE = os.getenv('MONGODB_DATABASE')
# MONGODB_COLLECTION = os.getenv('MONGODB_COLLECTION')

# if not all([MONGODB_URI, MONGODB_DATABASE, MONGODB_COLLECTION]):
#     raise Exception("MongoDB settings missing. Please set them in your .env file.")

# MongoDB
MONGODB_URI = os.getenv('MONGODB_URI', config.get('mongo_path'))
MONGODB_DATABASE = os.getenv('MONGODB_DATABASE', config.get('database'))
MONGODB_COLLECTION = os.getenv('MONGODB_COLLECTION', config.get('collection'))

if not all([MONGODB_URI, MONGODB_DATABASE, MONGODB_COLLECTION]):
    raise ValueError("MongoDB settings missing. Please set them in config.json or environment.")

MONGODB_CLIENT = MongoClient(MONGODB_URI)
METADATA_DB = MONGODB_CLIENT[MONGODB_DATABASE]
METADATA_COLLECTION = METADATA_DB[MONGODB_COLLECTION]

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
