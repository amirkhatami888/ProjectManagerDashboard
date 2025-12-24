from .settings import *

# Local development overrides
DEBUG = True

ALLOWED_HOSTS = [
	"127.0.0.1",
	"localhost",
]

# Disable HTTPS-only settings for local http:// testing
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
SESSION_SECURE_COOKIES = False
SESSION_CSRF_COOKIE_SECURE = False

# Add testserver to ALLOWED_HOSTS for testing
ALLOWED_HOSTS.extend([
    "testserver",
    "127.0.0.1:8000",
    "localhost:8000",
    "127.0.0.1",
    "localhost",
])

# MySQL Database Configuration for local development
# Note: If using environment variables, set DB_PASSWORD in .env file
# Otherwise, the password below will be used
DATABASES = {
    "default": {
        "ENGINE": config('DB_ENGINE', default="django.db.backends.mysql"),
        "NAME": config('DB_NAME', default="project_manager_db"),
        "USER": config('DB_USER', default="root"),
        "PASSWORD": config('DB_PASSWORD', default="Amir137667318@"),
        "HOST": config('DB_HOST', default="localhost"),
        "PORT": config('DB_PORT', default="3306"),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'use_unicode': True,
            'init_command': "SET NAMES 'utf8mb4' COLLATE 'utf8mb4_unicode_ci'",
            'sql_mode': 'STRICT_TRANS_TABLES',
        },
    }
}

# Ensure Persian language support in local development
LANGUAGE_CODE = "fa"  # Persian/Farsi
USE_L10N = True  # Enable localization

