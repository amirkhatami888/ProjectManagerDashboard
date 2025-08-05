"""
Production settings for project_dashboard project.
This file is used for production deployment.
"""

import os
from pathlib import Path
from decouple import config



# Build paths inside the project like this: BASE_DIR / 'subdir'.
# BASE_DIR = Path(__file__).resolve().parent.parent
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Security settings for production
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-this-in-production')

DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost').split(',')

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    
    # Third-party apps
    'crispy_forms',
    'crispy_bootstrap5',
    'jalali_date',
    
    # Custom apps
    'accounts',
    'dashboard',
    'creator_project',
    'creator_subproject',
    'creator_review',
    'reporter',
    'notifications',
    'notifications_sms',
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "project_dashboard.middleware.LoginRequiredMiddleware",
]

ROOT_URLCONF = "project_dashboard.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, 'templates')],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "project_dashboard.wsgi.application"

# Database configuration
# server
# DATABASES = {
#     "default": {
#         "ENGINE": config('DB_ENGINE', default="django.db.backends.mysql"),
#         "NAME": config('DB_NAME', default="amirho10_project_manager_db"),
#         "USER": config('DB_USER', default="	amirho10_amirkhatatmi888"),
#         "PASSWORD": config('DB_PASSWORD', default="Amir137667318@"),  # Use environment variable for security
#         "HOST": config('DB_HOST', default="localhost"),
#         "PORT": config('DB_PORT', default="3306"),
#         'OPTIONS': {
#             'charset': 'utf8mb4',
#             'use_unicode': True,
#             'init_command': "SET NAMES 'utf8mb4';",
#         },
#     }
# }
# local
DATABASES = {
    "default": {
        "ENGINE": config('DB_ENGINE', default="django.db.backends.mysql"),
        "NAME": config('DB_NAME', default="project_manager_db"),
        "USER": config('DB_USER', default="	root"),
        "PASSWORD": config('DB_PASSWORD', default="Amir137667318@"),
        "HOST": config('DB_HOST', default="localhost"),
        "PORT": config('DB_PORT', default="3388"),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'use_unicode': True,
            'init_command': "SET NAMES 'utf8mb4';",
        },
    }
}


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Tehran"
USE_I18N = True
USE_TZ = True

# Static files configuration
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

# Media files configuration
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Crispy Forms settings
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Custom user model
AUTH_USER_MODEL = 'accounts.User'

# Authentication settings
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = 'dashboard:dashboard'
LOGOUT_REDIRECT_URL = '/accounts/login/'

# Jalali Date configuration
JALALI_DATE_DEFAULTS = {
    'LIST_DISPLAY_AUTO_CONVERT': True,
    'Strftime': {
        'date': '%y/%m/%d',
        'datetime': '%H:%M:%S _ %y/%m/%d',
    },
    'Static': {
        'js': ['admin/js/django_jalali.min.js'],
        'css': {'all': ['admin/css/django_jalali.min.css']}
    },
}

# Security settings for production
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Additional production security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=False, cast=bool)

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Ensure logs and cache directories exist
os.makedirs(os.path.join(BASE_DIR, 'logs'), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, 'cache'), exist_ok=True) 