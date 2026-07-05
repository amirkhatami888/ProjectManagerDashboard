"""
Production settings for project_dashboard project.
Optimized for Windows Server 2025 with IIS deployment.
"""

import os
from pathlib import Path
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-this-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

# Production ALLOWED_HOSTS
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='ocmp.ir,www.ocmp.ir,localhost,127.0.0.1').split(',')

# Application definition (accounts first so custom createsuperuser is used)
INSTALLED_APPS = [
    "accounts",
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
    'django_extensions',
    
    # Custom apps
    'dashboard',
    'creator_program',
    'creator_project',
    'creator_subproject',
    'creator_review',
    'reporter',
    'webhooks',
    'activity_monitor',
    'session_manager',
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "accounts.brute_force_middleware.BruteForceProtectionMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "project_dashboard.middleware.LoginRequiredMiddleware",
    
    # Activity monitoring middleware
    "activity_monitor.middleware.ActivityTrackingMiddleware",
    "activity_monitor.middleware.LoginLogoutMiddleware",
    "activity_monitor.middleware.ProjectChangeMiddleware",
    "activity_monitor.middleware.SecurityMiddleware",
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


def _db_options():
    """DB OPTIONS with PyMySQL decimal fix to avoid decimal.ConversionSyntax (MariaDB).
    Use str for DECIMAL/NEWDECIMAL so the driver never calls float() on non-numeric
    values (e.g. password hashes or version strings) which causes ValueError on login.
    """
    opts = {
        'charset': 'utf8mb4',
        'use_unicode': True,
        'init_command': "SET NAMES 'utf8mb4' COLLATE 'utf8mb4_unicode_ci'",
        'sql_mode': 'STRICT_TRANS_TABLES',
        'connect_timeout': 60,
        'read_timeout': 60,
        'write_timeout': 60,
        'isolation_level': None,
        'autocommit': True,
    }
    try:
        import pymysql
        from pymysql.constants import FIELD_TYPE
        from pymysql.converters import conversions

        # Return DECIMAL/NEWDECIMAL as str to avoid float() on non-numeric values
        # (e.g. password hash or DB version string) which breaks login and event logging.
        conv = conversions.copy()
        conv[FIELD_TYPE.DECIMAL] = str
        conv[FIELD_TYPE.NEWDECIMAL] = str
        opts['conv'] = conv
    except ImportError:
        pass
    return opts

# Database configuration for production - MySQL/MariaDB
DATABASES = {
    "default": {
        "ENGINE": config('DB_ENGINE', default="django.db.backends.mysql"),
        "NAME": config('DB_NAME', default="ufvuikiv_project_manager_db"),
        "USER": config('DB_USER', default="ufvuikiv_amirkhatatmi888"),
        "PASSWORD": config('DB_PASSWORD', default="Amir137667318@"),
        "HOST": config('DB_HOST', default="localhost"),
        "PORT": config('DB_PORT', default="3306"),
        'OPTIONS':{**_db_options(),
        'init_command': "SET NAMES 'utf8mb4' COLLATE 'utf8mb4_unicode_ci', time_zone='+03:30'",},
        # Connection pooling settings - use 0 to disable persistent connections
        # This helps avoid "MySQL server has gone away" errors
        'CONN_MAX_AGE': 0,
        # Connection retry settings
        'ATOMIC_REQUESTS': False,
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
LANGUAGE_CODE = "fa"  # Persian/Farsi language code

# Supported languages
LANGUAGES = [
    ('fa', 'فارسی'),
    ('en', 'English'),
]

TIME_ZONE = "Asia/Tehran"
USE_I18N = True
USE_L10N = True  # Enable localization
USE_TZ = False

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# Media files (User uploaded files)
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

# Cloudflare Turnstile keys for the login page.
# Set these in the production environment or .env file.
TURNSTILE_SITE_KEY = config('TURNSTILE_SITE_KEY', default='').strip()
TURNSTILE_SECRET_KEY = config('TURNSTILE_SECRET_KEY', default='').strip()
TURNSTILE_VERIFY_URL = 'https://challenges.cloudflare.com/turnstile/v0/siteverify'

# Session settings for production
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 3600  # 1 hour
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=True, cast=bool)  # True for HTTPS
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_SAVE_EVERY_REQUEST = True

# Session Security Settings
SESSION_MAX_FAILED_ATTEMPTS = 5
SESSION_LOCKOUT_DURATION = 300  # 5 minutes
SESSION_SECURE_COOKIES = config('SESSION_SECURE_COOKIES', default=True, cast=bool)  # True for HTTPS
SESSION_CSRF_COOKIE_SECURE = config('SESSION_CSRF_COOKIE_SECURE', default=True, cast=bool)  # True for HTTPS
SESSION_CSRF_COOKIE_HTTPONLY = True
SESSION_CSRF_COOKIE_SAMESITE = 'Lax'

# Jalali Date configuration
JALALI_DATE_DEFAULTS = {
    'LIST_DISPLAY_AUTO_CONVERT': True,
    'Strftime': {
        'date': '%y/%m/%d',
        'datetime': '%H:%M:%S _ %y/%m/%d',
    },
    'Static': {
        'js': [
            'admin/js/django_jalali.min.js',
        ],
        'css': {
            'all': [
              'admin/css/django_jalali.min.css',
            ]
        }
    },
}

# Production Security Settings for IIS
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=False, cast=bool)  # False to disable HTTPS redirect
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000  # 1 year for production
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# Production Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'ERROR',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['file', 'console'],
            'level': 'ERROR',
            'propagate': True,
        },
        'creator_program': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Ensure proper Unicode handling
import sys
import locale

if sys.version_info[0] >= 3:
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Set locale to support UTF-8
try:
    locale.setlocale(locale.LC_ALL, 'fa_IR.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_ALL, 'Persian_Iran.UTF-8')
    except locale.Error:
        locale.setlocale(locale.LC_ALL, '')

# Add these settings to ensure proper Unicode handling
DEFAULT_CHARSET = 'utf-8'
FILE_CHARSET = 'utf-8'

# Production Cache Configuration (if using Redis or Memcached)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Email Configuration for Production
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='localhost')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='Amir137667318@')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@ocmp.ir')
