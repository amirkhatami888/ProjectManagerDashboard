#!/usr/bin/env python
"""
Create MySQL user using Django's database connection
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

def create_user():
    """Create MySQL user and grant privileges"""
    try:
        with connection.cursor() as cursor:
            # First, let's try to connect as root to create the user
            print("Attempting to create user 'amirkhatatmi888'...")
            
            # Try to create the user
            try:
                cursor.execute("CREATE USER 'amirkhatatmi888'@'localhost' IDENTIFIED BY 'Amir137667318@!'")
                print("✅ User 'amirkhatatmi888' created")
            except Exception as e:
                print(f"User creation error (may already exist): {e}")
            
            # Grant privileges
            try:
                cursor.execute("GRANT ALL PRIVILEGES ON project_manager_db.* TO 'amirkhatatmi888'@'localhost'")
                cursor.execute("FLUSH PRIVILEGES")
                print("✅ Privileges granted to 'amirkhatatmi888'")
            except Exception as e:
                print(f"Privilege grant error: {e}")
            
            # Test the connection with the new user
            print("Testing connection with new user...")
            cursor.execute("SELECT USER()")
            result = cursor.fetchone()
            print(f"✅ Connected as: {result[0]}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("You may need to run this as a MySQL administrator or check your MySQL configuration.")

if __name__ == "__main__":
    create_user()
