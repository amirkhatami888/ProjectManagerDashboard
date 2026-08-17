"""
WSGI configuration for cPanel/Passenger deployment
This file is used as the "Application startup file" in cPanel Python App setup.

cPanel Configuration:

  - Application root: public_html/PMD
  - Application URL: ocmp.ir
  - Startup file: passenger_wsgi.py
  - Entry point: application

  The deployed file must be:
  /home/ufvuikiv/public_html/PMD/passenger_wsgi.py

  This assumes manage.py and this file are uploaded directly inside
  public_html/PMD.
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

# Set these before Django is initialized.  Do not overwrite values supplied
# by an outer cPanel/Passenger wrapper: the filesystem directory (for example
# /home/.../PMD) is not necessarily the public URL prefix.  For an application
# mounted at https://ocmp.ir the correct defaults are /static/ and /media/.
os.environ.setdefault(
    'STATIC_URL',
    os.environ.get('DEPLOYMENT_STATIC_URL', '/static/'),
)
os.environ.setdefault(
    'MEDIA_URL',
    os.environ.get('DEPLOYMENT_MEDIA_URL', '/media/'),
)

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
        _django_application = get_wsgi_application()

        # Passenger/cPanel can route static URLs differently from Django.
        # Serve the login logo directly so it remains public and independent
        # of STATIC_URL, WhiteNoise, or LoginRequiredMiddleware.
        _logo_path = os.path.join(BASE_DIR, 'static', 'image', 'logo.png')

        def application(environ, start_response):
            request_path = environ.get('PATH_INFO', '').rstrip('/')
            if request_path in ('/site-logo', '/PMD/site-logo'):
                try:
                    with open(_logo_path, 'rb') as logo_file:
                        logo_data = logo_file.read()
                    start_response(
                        '200 OK',
                        [
                            ('Content-Type', 'image/png'),
                            ('Content-Length', str(len(logo_data))),
                            ('Cache-Control', 'public, max-age=3600'),
                        ],
                    )
                    return [logo_data]
                except OSError:
                    start_response(
                        '404 Not Found',
                        [('Content-Type', 'text/plain; charset=utf-8')],
                    )
                    return [b'Logo file not found']
            return _django_application(environ, start_response)
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
