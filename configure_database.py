#!/usr/bin/env python
"""
Database configuration script for Project Manager Dashboard
"""
import os
import sys

def configure_mysql():
    """Configure settings for MySQL"""
    settings_file = "project_dashboard/settings.py"
    
    # Read current settings
    with open(settings_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # MySQL configuration
    mysql_config = '''# MySQL Database Configuration
DATABASES = {
    "default": {
        "ENGINE": config('DB_ENGINE', default="django.db.backends.mysql"),
        "NAME": config('DB_NAME', default="project_manager_db"),
        "USER": config('DB_USER', default="root"),
        "PASSWORD": config('DB_PASSWORD', default="Amir137667318@"),
        "HOST": config('DB_HOST', default="localhost"),
        "PORT": config('DB_PORT', default="3306"),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'use_unicode': True,
            'init_command': "SET NAMES 'utf8mb4' COLLATE 'utf8mb4_unicode_ci'"
        },
    }
}'''
    
    # Replace database configuration
    import re
    pattern = r'# MySQL Database Configuration.*?}'
    new_content = re.sub(pattern, mysql_config, content, flags=re.DOTALL)
    
    # Write back to file
    with open(settings_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ MySQL configuration applied!")
    print("📋 Next steps:")
    print("   1. Install MySQL server")
    print("   2. Create database: project_manager_db")
    print("   3. Run: python manage.py migrate")

def configure_sqlite():
    """Configure settings for SQLite"""
    settings_file = "project_dashboard/settings.py"
    
    # Read current settings
    with open(settings_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # SQLite configuration
    sqlite_config = '''# SQLite Database Configuration (Development)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}'''
    
    # Replace database configuration
    import re
    pattern = r'# MySQL Database Configuration.*?}'
    new_content = re.sub(pattern, sqlite_config, content, flags=re.DOTALL)
    
    # Write back to file
    with open(settings_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ SQLite configuration applied!")
    print("📋 Next steps:")
    print("   1. Run: python manage.py migrate")
    print("   2. Run: python manage.py createsuperuser")

def main():
    print("🗄️  Database Configuration for Project Manager Dashboard")
    print("=" * 60)
    print("Choose your database:")
    print("1. MySQL (Production recommended)")
    print("2. SQLite (Development/Testing)")
    print("3. Exit")
    
    while True:
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == '1':
            configure_mysql()
            break
        elif choice == '2':
            configure_sqlite()
            break
        elif choice == '3':
            print("👋 Goodbye!")
            sys.exit(0)
        else:
            print("❌ Invalid choice. Please enter 1, 2, or 3.")

if __name__ == "__main__":
    main()
