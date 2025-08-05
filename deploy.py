#!/usr/bin/env python3
"""
Production Deployment Script for Django Project Manager Dashboard

This script helps prepare your Django application for production deployment.
Run this script to:
1. Generate a secure SECRET_KEY
2. Create environment variables template
3. Run security checks
4. Collect static files
5. Check database connectivity

Usage:
    python deploy.py --check         # Run security checks only
    python deploy.py --prepare      # Prepare for deployment
    python deploy.py --collect      # Collect static files
    python deploy.py --all          # Do everything
"""

import os
import sys
import argparse
from django.core.management.utils import get_random_secret_key
from django.conf import settings

def generate_secure_key():
    """Generate a secure SECRET_KEY for production"""
    return get_random_secret_key()

def create_env_template():
    """Create a .env template file"""
    secret_key = generate_secure_key()
    
    env_content = f"""# Production Environment Variables
# Copy this file to .env and update the values for your production environment

# Django Settings
SECRET_KEY={secret_key}
DEBUG=False
DJANGO_SETTINGS_MODULE=project_dashboard.production_settings

# Domain Configuration (REQUIRED - Replace with your actual domain)
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database Configuration (REQUIRED - Update with your production database)
DB_ENGINE=django.db.backends.mysql
DB_NAME=your_production_database_name
DB_USER=your_production_db_user
DB_PASSWORD=your_production_db_password
DB_HOST=localhost
DB_PORT=3306

# Static and Media Files
STATIC_URL=/static/
MEDIA_URL=/media/

# Security Settings (Enable for HTTPS)
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True

# Email Configuration (Optional)
EMAIL_HOST=smtp.your-provider.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@domain.com
EMAIL_HOST_PASSWORD=your-email-password

# Cache Configuration (Optional - for Redis)
REDIS_URL=redis://localhost:6379/1
"""
    
    with open('.env.template', 'w') as f:
        f.write(env_content)
    
    print("✅ Created .env.template with secure SECRET_KEY")
    print("📝 Please copy .env.template to .env and update the values for your environment")
    return secret_key

def run_security_check():
    """Run Django security checks"""
    print("\n🔍 Running Django Security Checks...")
    exit_code = os.system('python manage.py check --deploy')
    
    if exit_code == 0:
        print("✅ Security checks passed!")
    else:
        print("⚠️  Security issues found. Please review the warnings above.")
    
    return exit_code == 0

def collect_static_files():
    """Collect static files for production"""
    print("\n📦 Collecting static files...")
    exit_code = os.system('python manage.py collectstatic --noinput')
    
    if exit_code == 0:
        print("✅ Static files collected successfully!")
    else:
        print("❌ Failed to collect static files.")
    
    return exit_code == 0

def check_database():
    """Check database connectivity"""
    print("\n🗄️  Checking database connectivity...")
    
    # Check if we're in development mode (no .env file exists)
    if not os.path.exists('.env'):
        print("⚠️  No .env file found - using development database settings")
        print("💡 For production deployment, create .env file with your database credentials")
        return True  # Skip database check in development
    
    exit_code = os.system('python manage.py migrate --check')
    
    if exit_code == 0:
        print("✅ Database connectivity check passed!")
    else:
        print("❌ Database connectivity issues. Please check your database configuration.")
        print("💡 Make sure your .env file has correct database credentials")
    
    return exit_code == 0

def print_deployment_checklist():
    """Print deployment checklist"""
    print("\n" + "="*60)
    print("📋 PRODUCTION DEPLOYMENT CHECKLIST")
    print("="*60)
    print("Before deploying to production, ensure you have:")
    print("  ✅ Created .env file with production values")
    print("  ✅ Set DEBUG=False in your .env file")
    print("  ✅ Updated ALLOWED_HOSTS with your domain")
    print("  ✅ Updated database credentials")
    print("  ✅ Configured SSL certificate (HTTPS)")
    print("  ✅ Set up proper web server (Nginx/Apache)")
    print("  ✅ Configured firewall settings")
    print("  ✅ Set up backup strategy")
    print("  ✅ Tested deployment in staging environment")
    print("="*60)

def main():
    parser = argparse.ArgumentParser(description='Django Production Deployment Helper')
    parser.add_argument('--check', action='store_true', help='Run security checks only')
    parser.add_argument('--prepare', action='store_true', help='Prepare for deployment')
    parser.add_argument('--collect', action='store_true', help='Collect static files')
    parser.add_argument('--all', action='store_true', help='Run all deployment preparations')
    
    args = parser.parse_args()
    
    if not any([args.check, args.prepare, args.collect, args.all]):
        args.all = True  # Default to all if no specific option chosen
    
    print("🚀 Django Production Deployment Helper")
    print("="*50)
    
    success = True
    
    if args.prepare or args.all:
        print("\n📝 Creating environment template...")
        secret_key = create_env_template()
        print(f"🔑 Generated secure SECRET_KEY: {secret_key[:20]}...")
    
    if args.check or args.all:
        success &= run_security_check()
    
    if args.collect or args.all:
        success &= collect_static_files()
    
    if args.all:
        success &= check_database()
        print_deployment_checklist()
    
    if success:
        print("\n🎉 All checks passed! Your application is ready for production deployment.")
        print("📖 See DEPLOYMENT_GUIDE.md for detailed deployment instructions.")
    else:
        print("\n⚠️  Some issues were found. Please fix them before deploying to production.")
        sys.exit(1)

if __name__ == '__main__':
    # Setup Django environment
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project_dashboard.settings')
    
    import django
    django.setup()
    
    main() 