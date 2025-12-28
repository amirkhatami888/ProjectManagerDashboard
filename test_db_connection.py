#!/usr/bin/env python
"""
Test database connection on cPanel server
Run this to verify your database configuration is correct
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project_dashboard.production_settings')
django.setup()

from django.db import connection
from django.conf import settings

def test_connection():
    """Test database connection"""
    print("=" * 60)
    print("Testing Database Connection")
    print("=" * 60)
    
    # Display configuration (without password)
    db_config = settings.DATABASES['default']
    print(f"\n📋 Database Configuration:")
    print(f"   Engine: {db_config['ENGINE']}")
    print(f"   Name: {db_config['NAME']}")
    print(f"   User: {db_config['USER']}")
    print(f"   Host: {db_config['HOST']}")
    print(f"   Port: {db_config['PORT']}")
    print(f"   Password: {'*' * len(str(db_config.get('PASSWORD', '')))}")
    
    try:
        # Test connection
        print("\n🔌 Testing connection...")
        connection.ensure_connection()
        print("✅ Database connection successful!")
        
        # Get database version
        with connection.cursor() as cursor:
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()[0]
            print(f"📊 MySQL Version: {version}")
            
            # Check if database exists
            cursor.execute("SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = %s", 
                          [db_config['NAME']])
            db_exists = cursor.fetchone()
            
            if db_exists:
                print(f"✅ Database '{db_config['NAME']}' exists")
            else:
                print(f"⚠️  Database '{db_config['NAME']}' does NOT exist!")
                print(f"   Create it with: CREATE DATABASE {db_config['NAME']} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Database connection failed!")
        print(f"   Error: {e}")
        print("\n🔧 Troubleshooting:")
        print("   1. Check .env file exists and has correct values")
        print("   2. Verify database credentials in .env file")
        print("   3. Make sure database exists")
        print("   4. Check MySQL user has proper permissions")
        return False

if __name__ == "__main__":
    try:
        success = test_connection()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

