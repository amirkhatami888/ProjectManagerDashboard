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

# MUST run before any other imports: use PyMySQL as MySQLdb so DECIMAL columns
# return str (avoids "could not convert string to float" on login with MariaDB).
_PYMYSQL_PATCHED = False
try:
    import pymysql
    pymysql.install_as_MySQLdb()
    from pymysql.constants import FIELD_TYPE
    from pymysql.converters import conversions
    _conv = conversions.copy()
    _conv[FIELD_TYPE.DECIMAL] = str
    _conv[FIELD_TYPE.NEWDECIMAL] = str
    pymysql.converters.conversions = _conv
    _PYMYSQL_PATCHED = True
except Exception:
    pass

import sys
import os

# Define application immediately so Passenger always sees it (even if setup fails later)
def application(environ, start_response):
    if not _PYMYSQL_PATCHED:
        start_response("503 Service Unavailable", [("Content-Type", "text/plain; charset=utf-8")])
        return [b"PyMySQL required for MariaDB. In virtualenv run: pip install PyMySQL"]
    start_response("500 Internal Server Error", [("Content-Type", "text/plain; charset=utf-8")])
    return [b"WSGI startup failed. Check server error logs for traceback."]

# Get project root directory (where this file is located)
# This ensures the path is correct regardless of where Python is executed from
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Add project root to Python path
# This allows Django to find your project modules
sys.path.insert(0, BASE_DIR)

# Change working directory to project root
# This ensures relative paths in Django settings work correctly
os.chdir(BASE_DIR)

# Use production settings on cPanel/Passenger and keep DEBUG disabled by default.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project_dashboard.production_settings')
os.environ.setdefault('DEBUG', 'False')

# Load Django only when PyMySQL is patched (otherwise login 500s with MariaDB)
if _PYMYSQL_PATCHED:
    try:
        # Passenger does not run Django management commands during deployment.
        # STATIC_ROOT is intentionally ignored by git, so collect the checked-in
        # files from static/ before serving the application.  Without this step
        # production returns 404 for assets such as static/image/logo.png while
        # DEBUG-mode local development can still find them directly.
        import django
        django.setup()
        from django.core.management import call_command
        call_command('collectstatic', interactive=False, verbosity=0)

        from django.core.wsgi import get_wsgi_application
        application = get_wsgi_application()
    except Exception as e:
        import traceback
        _startup_error = traceback.format_exc()

        def _error_app(environ, start_response):
            status = "500 Internal Server Error"
            body = (
                "Application failed to start.\n\n"
                "Error:\n" + str(e) + "\n\nTraceback:\n" + _startup_error
            ).encode("utf-8")
            start_response(status, [("Content-Type", "text/plain; charset=utf-8")])
            return [body]
        application = _error_app
