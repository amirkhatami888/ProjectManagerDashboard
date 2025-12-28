import sys
import os

# Use PyMySQL as MySQLdb replacement (better MariaDB compatibility)
try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass  # MySQLdb will be used if PyMySQL is not available

# Get project root directory (where this file is located)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Add to Python path
sys.path.insert(0, BASE_DIR)

# Change to project directory
os.chdir(BASE_DIR)

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project_dashboard.production_settings')

# Import WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
