"""
WSGI config for project_dashboard project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
from django.core.wsgi import get_wsgi_application

# Use production settings if DJANGO_SETTINGS_MODULE is not set and we're in production
# This allows for easy switching between development and production environments
settings_module = os.environ.get('DJANGO_SETTINGS_MODULE', 'project_dashboard.settings')

# If running on a server (common production indicators), use production settings
if any([
    os.environ.get('SERVER_SOFTWARE'),  # Common in many hosting environments
    os.environ.get('WEBSITE_HOSTNAME'),  # Azure
    os.environ.get('DYNO'),  # Heroku
    os.environ.get('PLATFORM_PROJECT_NAME'),  # Platform.sh
    os.environ.get('LIARA_URL'),  # Liara
    os.environ.get('DJANGO_ENV') == 'production',  # Custom environment variable
]):
    settings_module = 'project_dashboard.production_settings'

os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_module)

application = get_wsgi_application()
