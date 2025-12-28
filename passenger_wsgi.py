"""
Passenger WSGI entry point for cPanel deployment
This file is used by cPanel's Python App setup as the Application startup file
"""
import sys
import os

# Add the project directory to Python path
# This ensures Django can find all modules
project_dir = os.path.dirname(os.path.abspath(__file__))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

# Set the Django settings module to production settings
# This can be overridden by .env file if present
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project_dashboard.production_settings')

# Import the WSGI application from Django
# This is the 'application' object that cPanel will use
from project_dashboard.wsgi import application
