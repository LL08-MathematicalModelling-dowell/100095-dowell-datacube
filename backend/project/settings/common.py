"""
Django settings for the DataCube project that are common to all environments.
"""
import os
from pathlib import Path
from datetime import timedelta
from pymongo import AsyncMongoClient, MongoClient  # type: ignore
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
INTERNAL_IPS = []

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
SYNC_MONGODB_CLIENT = MongoClient(MONGODB_URI)
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
        'core.infrastructure.authentication.CustomJWTAuthentication',
        'core.infrastructure.authentication.APIKeyAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'UNAUTHENTICATED_USER': None,
    'DEFAULT_THROTTLE_RATES': {
        'otp': '60/hour',
        'login': '30/minute',
        'register': '20/minute',
        'oauth': '40/minute',
        'demo_login': '10/minute',
        'password_reset': '15/hour',
        'token_refresh': '90/minute',
        'user_burst': '2000/hour',
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=7),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=14),
    # Blacklist + rotation require Django User FK on OutstandingToken — incompatible with Mongo users.
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": False,
    "UPDATE_LAST_LOGIN": False,
    "TOKEN_REFRESH_SERIALIZER": "core.infrastructure.jwt_serializers.DatacubeTokenRefreshSerializer",
    "CHECK_USER_IS_ACTIVE": False,
}

# --- OTP (hashed at rest with OTP_PEPPER) ---
OTP_LENGTH = int(os.getenv("OTP_LENGTH", "6"))
OTP_EXPIRES_MINUTES = int(os.getenv("OTP_EXPIRES_MINUTES", "10"))
OTP_MAX_ATTEMPTS = int(os.getenv("OTP_MAX_ATTEMPTS", "5"))
OTP_PEPPER = os.getenv(
    "OTP_PEPPER",
    "dev-only-otp-pepper-change-me-please-change-me-please",
)

# --- Email (Resend) & OAuth (server-side PKCE code exchange) ---
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
RESEND_FROM_EMAIL = os.getenv("RESEND_FROM_EMAIL", "onboarding@resend.dev")
RESEND_FROM_NAME = os.getenv("RESEND_FROM_NAME", "DataCube")
ALLOW_STDOUT_EMAIL = os.getenv("ALLOW_STDOUT_EMAIL", "").lower() in ("1", "true", "yes")
GOOGLE_OAUTH_CLIENT_ID = os.getenv("GOOGLE_OAUTH_CLIENT_ID", "")
GOOGLE_OAUTH_CLIENT_SECRET = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", "")
GITHUB_OAUTH_CLIENT_ID = os.getenv("GITHUB_OAUTH_CLIENT_ID", "")
GITHUB_OAUTH_CLIENT_SECRET = os.getenv("GITHUB_OAUTH_CLIENT_SECRET", "")

# Demo login: set DEMO_AUTO_ENSURE_USER=1 in development to auto-create a verified demo user in Mongo.
DEMO_LOGIN_EMAIL = os.getenv("DEMO_LOGIN_EMAIL", "samanta@dowellresearch.se")
DEMO_AUTO_ENSURE_USER = os.getenv("DEMO_AUTO_ENSURE_USER", "").lower() in ("1", "true", "yes")

# When True, BaseAPIView._track skips telemetry for /api/v2/* (middleware already logs).
ANALYTICS_DISABLE_VIEW_TELEMETRY_FOR_API_V2 = (
    os.getenv("ANALYTICS_DISABLE_VIEW_TELEMETRY_FOR_API_V2", "true").lower()
    in ("1", "true", "yes")
)

DEMO_PLAYGROUND_SECRET = os.getenv("DEMO_PLAYGROUND_SECRET", "DEMO_PLAYGROUND_SECRET_DUMMY")
