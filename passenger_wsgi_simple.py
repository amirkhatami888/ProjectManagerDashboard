import sys
import os

# Get the directory where this file is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Add BASE_DIR to Python path
sys.path.insert(0, BASE_DIR)

# Change working directory to BASE_DIR
os.chdir(BASE_DIR)

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project_dashboard.production_settings')

# Import Django WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

