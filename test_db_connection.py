#!/usr/bin/env python
"""
Test database connection using Django settings
"""
import os
import sys
import django
from django.conf import settings

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project_dashboard.production_settings')
django.setup()

from django.db import connection

try:
    # Test the connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        print("✅ Database connection successful!")
        print(f"Test query result: {result}")
        
        # Check if database exists
        cursor.execute("SHOW DATABASES LIKE 'project_manager_db'")
        db_exists = cursor.fetchone()
        if db_exists:
            print("✅ Database 'project_manager_db' exists")
        else:
            print("❌ Database 'project_manager_db' does not exist")
            # Create the database
            cursor.execute("CREATE DATABASE IF NOT EXISTS project_manager_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print("✅ Database 'project_manager_db' created")
            
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    print(f"Connection details:")
    print(f"  Host: {settings.DATABASES['default']['HOST']}")
    print(f"  Port: {settings.DATABASES['default']['PORT']}")
    print(f"  User: {settings.DATABASES['default']['USER']}")
    print(f"  Database: {settings.DATABASES['default']['NAME']}")
