#!/usr/bin/env python
"""
Create .env file for cPanel deployment
Run this script on your cPanel server to set up environment variables
"""
import os
from django.core.management.utils import get_random_secret_key

def create_env_file():
    """Create .env file with production settings"""
    
    # Generate secure SECRET_KEY
    secret_key = get_random_secret_key()
    
    # Get domain from user or use placeholder
    domain = input("Enter your domain name (e.g., yourdomain.com): ").strip()
    if not domain:
        domain = "yourdomain.com"
        print("⚠️  Using placeholder domain. Please update .env file manually!")
    
    env_content = f"""# Production Environment Variables for cPanel
# Generated automatically - DO NOT commit this file to version control!

# Django Settings
SECRET_KEY={secret_key}
DEBUG=False
DJANGO_SETTINGS_MODULE=project_dashboard.production_settings

# Domain Configuration
ALLOWED_HOSTS={domain},www.{domain}

# Database Configuration - cPanel MySQL
DB_ENGINE=django.db.backends.mysql
DB_NAME=ufvuikiv_project_manager_db
DB_USER=ufvuikiv_amirkhatatmi888
DB_PASSWORD=Amir137667318@
DB_HOST=localhost
DB_PORT=3306

# Static and Media Files
STATIC_URL=/static/
MEDIA_URL=/media/

# Security Settings (Enable for HTTPS)
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SESSION_SECURE_COOKIES=True
SESSION_CSRF_COOKIE_SECURE=True

# Email Configuration (Optional)
EMAIL_HOST=localhost
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
"""
    
    # Write .env file
    with open('.env', 'w') as f:
        f.write(env_content)
    
    # Set secure permissions (read/write for owner only)
    os.chmod('.env', 0o600)
    
    print("✅ .env file created successfully!")
    print(f"📝 Domain set to: {domain}")
    print("🔒 File permissions set to 600 (read/write for owner only)")
    print("\n📋 Next steps:")
    print("   1. Verify database exists: mysql -u ufvuikiv_amirkhatatmi888 -p'Amir137667318@' -e 'SHOW DATABASES;'")
    print("   2. Run migrations: python manage.py migrate")
    print("   3. Collect static files: python manage.py collectstatic --noinput")
    print("   4. Create superuser: python manage.py createsuperuser")
    print("   5. Restart Python app in cPanel")

if __name__ == "__main__":
    if os.path.exists('.env'):
        response = input("⚠️  .env file already exists. Overwrite? (y/N): ").strip().lower()
        if response != 'y':
            print("❌ Cancelled. Existing .env file preserved.")
            exit(0)
    
    create_env_file()

