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

# SQLite fallback for development
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

