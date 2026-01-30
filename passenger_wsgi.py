"""
Passenger WSGI entry point for server deployment.
Use this file on the server (e.g. in public_html/PMD or your app root).
Ensures MySQL/MariaDB decimal and datetime fixes run before any Django/DB code.
"""
import os
import sys

# Add your Django project directory to sys.path (project root = where fix_decimal_error.py and project_dashboard live)
PROJECT_ROOT = '/home/ufvuikiv/public_html/PMD/ProjectManagerDashboard'
sys.path.insert(0, PROJECT_ROOT)

# Point Django to the correct settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project_dashboard.settings')
# If you want to force production settings, use:
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project_dashboard.production_settings')

# Apply MySQL/MariaDB fixes BEFORE importing Django app (patches MySQLdb converters)
import fix_decimal_error  # noqa: F401

# Import the WSGI application (this loads Django and get_wsgi_application())
from project_dashboard.wsgi import application

# Patch Django's MySQL backend after Django is loaded (decimals + datetime-as-string)
fix_decimal_error.patch_django_mysql_backend()


#check it right 