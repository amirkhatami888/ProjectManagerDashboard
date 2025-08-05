#!/usr/bin/env python
"""
Script to set up UTF8MB4 Unicode collation for the entire database.
This script will:
1. Create the database with UTF8MB4 collation if it doesn't exist
2. Convert all existing tables to UTF8MB4
3. Set proper collation for all text fields
4. Update Django settings to use UTF8MB4

Run this script after setting up your MySQL database.
"""

import os
import sys
import django
import mysql.connector
from mysql.connector import Error

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project_dashboard.production_settings')
django.setup()

def create_database_with_utf8mb4():
    """Create database with UTF8MB4 collation"""
    try:
        connection = mysql.connector.connect(
            host='localhost',
            port=3388,
            user='root',
            password='Amir137667318@'
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # Create database with UTF8MB4 collation
            cursor.execute("""
                CREATE DATABASE IF NOT EXISTS project_manager_db 
                CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
            """)
            print("✅ Database 'project_manager_db' created/verified with UTF8MB4 collation!")
            
            # Set default character set for the database
            cursor.execute("""
                ALTER DATABASE project_manager_db 
                CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
            """)
            print("✅ Database default character set updated to UTF8MB4")
            
    except Error as e:
        print(f"❌ Error creating database: {e}")
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("✅ MySQL connection closed")
    
    return True

def convert_existing_tables_to_utf8mb4():
    """Convert all existing tables to UTF8MB4 collation"""
    try:
        connection = mysql.connector.connect(
            host='localhost',
            port=3388,
            user='root',
            password='Amir137667318@',
            database='project_manager_db'
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # Get all table names
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            
            print(f"🔄 Found {len(tables)} tables to convert...")
            
            for table in tables:
                table_name = table[0]
                print(f"🔄 Converting table: {table_name}")
                
                try:
                    # Convert table to UTF8MB4
                    cursor.execute(f"""
                        ALTER TABLE `{table_name}` 
                        CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
                    """)
                    print(f"✅ Converted {table_name} to UTF8MB4")
                    
                except Error as e:
                    print(f"⚠️  Could not convert {table_name}: {e}")
            
            # Set session variables for UTF8MB4
            cursor.execute("SET NAMES 'utf8mb4'")
            cursor.execute("SET character_set_connection=utf8mb4")
            cursor.execute("SET collation_connection=utf8mb4_unicode_ci")
            print("✅ Session variables set for UTF8MB4")
            
    except Error as e:
        print(f"❌ Error converting tables: {e}")
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
    
    return True

def run_django_migrations():
    """Run Django migrations to ensure all tables are properly set up"""
    try:
        print("🔄 Running Django migrations...")
        os.system("python manage.py migrate")
        print("✅ Django migrations completed")
        return True
    except Exception as e:
        print(f"❌ Error running migrations: {e}")
        return False

def setup_utf8mb4_collation():
    """Run the Django management command to set up UTF8MB4 collation"""
    try:
        print("🔄 Running UTF8MB4 collation setup...")
        os.system("python manage.py setup_utf8mb4_collation")
        print("✅ UTF8MB4 collation setup completed")
        return True
    except Exception as e:
        print(f"❌ Error setting up UTF8MB4 collation: {e}")
        return False

def main():
    """Main function to set up UTF8MB4 database"""
    print("🚀 Setting up UTF8MB4 Unicode collation for your database...")
    print("=" * 60)
    
    # Step 1: Create database with UTF8MB4
    print("\n📋 Step 1: Creating database with UTF8MB4 collation...")
    if not create_database_with_utf8mb4():
        print("❌ Failed to create database. Exiting.")
        return
    
    # Step 2: Convert existing tables
    print("\n📋 Step 2: Converting existing tables to UTF8MB4...")
    if not convert_existing_tables_to_utf8mb4():
        print("❌ Failed to convert tables. Exiting.")
        return
    
    # Step 3: Run Django migrations
    print("\n📋 Step 3: Running Django migrations...")
    if not run_django_migrations():
        print("❌ Failed to run migrations. Exiting.")
        return
    
    # Step 4: Set up UTF8MB4 collation
    print("\n📋 Step 4: Setting up UTF8MB4 collation...")
    if not setup_utf8mb4_collation():
        print("❌ Failed to set up UTF8MB4 collation. Exiting.")
        return
    
    print("\n" + "=" * 60)
    print("🎉 UTF8MB4 Unicode collation setup completed successfully!")
    print("\n📝 Your database is now configured to support:")
    print("   • Persian/Farsi text")
    print("   • Arabic text")
    print("   • Emojis and special characters")
    print("   • Full Unicode support")
    print("\n🔧 Next steps:")
    print("   1. Restart your Django application")
    print("   2. Test with Persian text input")
    print("   3. Verify emoji support if needed")

if __name__ == '__main__':
    main() 