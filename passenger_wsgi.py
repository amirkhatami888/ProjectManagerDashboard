"""
WSGI configuration for cPanel/Passenger deployment
This file is used as the "Application startup file" in cPanel Python App setup.

cPanel Configuration (avoid double path – use ONE of these):

  Option A – App under public_html/PMD:
  - Application root: PMD/ProjectManagerDashboard
    (relative to your home dir; full path = ~/PMD/ProjectManagerDashboard)
  - Startup file: passenger_wsgi.py
  - Entry point: application

  Option B – If your app is inside public_html already:
  - Application root: public_html/PMD/ProjectManagerDashboard
    (do NOT set root to "public_html/PMD" and then add "public_html/PMD" again)
  - Startup file: passenger_wsgi.py
  - Entry point: application

  The path to this file must be exactly:
  /home/ufvuikiv/public_html/PMD/ProjectManagerDashboard/passenger_wsgi.py
  (no duplicate "public_html/PMD" in the path).
"""

import sys
import os

# Use PyMySQL as MySQLdb replacement (better MariaDB compatibility)
# This is important for cPanel MySQL/MariaDB databases
try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass  # MySQLdb will be used if PyMySQL is not available

# Get project root directory (where this file is located)
# This ensures the path is correct regardless of where Python is executed from
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Add project root to Python path
# This allows Django to find your project modules
sys.path.insert(0, BASE_DIR)

# Change working directory to project root
# This ensures relative paths in Django settings work correctly
os.chdir(BASE_DIR)

# Set Django settings module for production
# Use production_settings for cPanel deployment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project_dashboard.production_settings')

# Import and create WSGI application
# This is the entry point that cPanel/Passenger will call
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
