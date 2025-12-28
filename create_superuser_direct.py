#!/usr/bin/env python
"""
Create superuser directly using Django ORM
This avoids connection timeout issues
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project_dashboard.production_settings')
django.setup()

from accounts.models import User

def create_superuser():
    """Create superuser directly"""
    print("Creating superuser...")
    
    username = input("Username: ").strip()
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
        print(f"✅ Superuser '{username}' created successfully!")
        return True
    except Exception as e:
        print(f"❌ Error creating superuser: {e}")
        return False

if __name__ == "__main__":
    try:
        create_superuser()
    except KeyboardInterrupt:
        print("\n❌ Cancelled.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

