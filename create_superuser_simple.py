#!/usr/bin/env python
"""
Create superuser - simple version without django_extensions dependency
"""
import os
import sys

# Use PyMySQL as MySQLdb replacement (better MariaDB compatibility)
try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass  # MySQLdb will be used if PyMySQL is not available

# Setup Django before importing models
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project_dashboard.production_settings')

# Temporarily remove django_extensions if it causes issues
import django
from django.conf import settings

# Remove django_extensions from INSTALLED_APPS if not installed
if 'django_extensions' in settings.INSTALLED_APPS:
    try:
        import django_extensions
    except ImportError:
        settings.INSTALLED_APPS.remove('django_extensions')

django.setup()

from accounts.models import User

def create_superuser():
    """Create superuser directly"""
    print("=" * 60)
    print("Create Superuser")
    print("=" * 60)
    
    username = input("\nUsername: ").strip()
    if not username:
        print("❌ Username is required!")
        return False
    
    # Check if user exists
    if User.objects.filter(username=username).exists():
        print(f"❌ User '{username}' already exists!")
        return False
    
    email = input("Email (optional): ").strip()
    password = input("Password: ").strip()
    if not password:
        print("❌ Password is required!")
        return False
    
    # Confirm password
    password2 = input("Password (again): ").strip()
    if password != password2:
        print("❌ Passwords don't match!")
        return False
    
    # Create superuser
    try:
        user = User.objects.create_user(
            username=username,
            email=email if email else f"{username}@example.com",
            password=password,
            is_staff=True,
            is_superuser=True,
            is_active=True
        )
        print(f"\n✅ Superuser '{username}' created successfully!")
        print(f"   Email: {user.email}")
        print(f"   Staff: {user.is_staff}")
        print(f"   Superuser: {user.is_superuser}")
        return True
    except Exception as e:
        print(f"\n❌ Error creating superuser: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        create_superuser()
    except KeyboardInterrupt:
        print("\n❌ Cancelled.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

