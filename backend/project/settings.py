"""Django settings for the project."""

import os
import json
from pathlib import Path
from pymongo import MongoClient


import mongoengine

# MongoDB Configuration (update with your actual MongoDB URI)
mongoengine.connect(
    db='datacube_db',  # The database name
    host='mongodb://localhost:27017'  # MongoDB connection URI
)

# Base directory setup
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_DIR_PATH = Path(BASE_DIR)

# Load config
config_path = BASE_DIR_PATH / 'config.json'
with open(config_path, encoding='utf-8') as f:
    config = json.load(f)

# MongoDB Configuration
MONGODB_URI = config['mongo_path']
MONGODB_DATABASE = config['database']
MONGODB_COLLECTION = config['collection']
MONGODB_CLIENT = MongoClient(MONGODB_URI)
METADATA_DB = MONGODB_CLIENT[MONGODB_DATABASE]
METADATA_COLLECTION = METADATA_DB[MONGODB_COLLECTION]

AUTHENTICATION_SERVICE_URL = 'http://localhost:8000/'

# Django Settings
SECRET_KEY = 'django-insecure-%vs+xh0tfg#)hoyl!!_j7epqz5+56@3pw1*k0_k90&6lnwvfb#'
DEBUG = True

INSTALLED_APPS = [
    # Django apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes', 
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    
    # Third party apps
    'corsheaders',
    'rest_framework',
    
    # Local apps
    'api',
]

SITE_ID = 1
REST_USE_JWT = True



# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
#         'USER': '',
#         'PASSWORD': '',
#         'HOST': '',
#         'PORT': '',
#     }
# }




MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    # 'api.middleware.APIKeyAuthenticationMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# URLs and Templates
ROOT_URLCONF = 'project.urls'
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
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


# Application Configuration
WSGI_APPLICATION = 'project.wsgi.application'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


ALLOWED_HOSTS = [
    'datacube.uxlivinglab.online',
    '127.0.0.1',
    'localhost', 
    'www.dowelldatacube.uxlivinglab.online',
    'dowelldatacube.uxlivinglab.online',
]


# CORS Settings
CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_HEADERS = ['*']


# Localization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static Files
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Other Settings
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
MY_BASE_URL = 'https://datacube.uxlivinglab.online'


# REST Framework Settings
REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
}



# Logging Configuration
BASE_DIR = Path(__file__).resolve().parent.parent
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR, exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOGS_DIR, 'database_operations.log'),
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'database_operations': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
