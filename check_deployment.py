#!/usr/bin/env python3
"""
Django Project Manager Dashboard - Deployment Status Checker
This script checks if your Django deployment is configured correctly.
Execute this in your cPanel Python App interface.
"""

import os
import sys
import django
from django.core.management import execute_from_command_line

def print_status(message, status="INFO"):
    """Print formatted status message"""
    symbols = {
        "INFO": "ℹ️",
        "SUCCESS": "✅", 
        "ERROR": "❌",
        "WARNING": "⚠️"
    }
    print(f"{symbols.get(status, 'ℹ️')} {message}")

def check_file_exists(filepath, description):
    """Check if a file exists"""
    if os.path.exists(filepath):
        print_status(f"{description} found", "SUCCESS")
        return True
    else:
        print_status(f"{description} missing", "ERROR")
        return False

def check_environment():
    """Check environment configuration"""
    print_status("Checking environment configuration...", "INFO")
    print("-" * 40)
    
    # Check .env file
    env_exists = check_file_exists('.env', '.env file')
    
    # Check Django settings
    settings_module = os.environ.get('DJANGO_SETTINGS_MODULE', 'project_dashboard.settings')
    print_status(f"Django settings module: {settings_module}", "INFO")
    
    # Check Python version
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    print_status(f"Python version: {python_version}", "INFO")
    
    return env_exists

def check_django_setup():
    """Check Django configuration"""
    print_status("Checking Django configuration...", "INFO")
    print("-" * 40)
    
    try:
        # Set Django settings
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project_dashboard.production_settings')
        
        # Setup Django
        django.setup()
        print_status("Django setup successful", "SUCCESS")
        
        # Check database connection
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        print_status("Database connection successful", "SUCCESS")
        
        # Check installed apps
        from django.conf import settings
        app_count = len(settings.INSTALLED_APPS)
        print_status(f"Installed apps: {app_count}", "INFO")
        
        # Check static files
        static_root = getattr(settings, 'STATIC_ROOT', None)
        if static_root and os.path.exists(static_root):
            print_status("Static files directory exists", "SUCCESS")
        else:
            print_status("Static files directory missing (run collect_static.py)", "WARNING")
        
        return True
        
    except Exception as e:
        print_status(f"Django setup failed: {e}", "ERROR")
        return False

def check_deployment_readiness():
    """Check if deployment is ready"""
    print_status("Checking deployment readiness...", "INFO")
    print("-" * 40)
    
    try:
        # Run Django's deployment check
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project_dashboard.production_settings')
        django.setup()
        
        from django.core.management import call_command
        from io import StringIO
        
        output = StringIO()
        call_command('check', '--deploy', stdout=output, stderr=output)
        
        result = output.getvalue()
        if "System check identified no issues" in result:
            print_status("Django deployment check passed", "SUCCESS")
        else:
            print_status("Django deployment check found issues", "WARNING")
            print("Details:")
            print(result)
        
        return True
        
    except Exception as e:
        print_status(f"Deployment check failed: {e}", "ERROR")
        return False

def main():
    """Main deployment check function"""
    print_status("Django Project Manager Dashboard - Deployment Check", "INFO")
    print("="*60)
    
    # Check current directory
    current_dir = os.getcwd()
    print_status(f"Current directory: {current_dir}", "INFO")
    
    # Check required files
    print()
    required_files = [
        ('manage.py', 'Django management script'),
        ('passenger_wsgi.py', 'WSGI configuration file'),
        ('.htaccess', 'Apache configuration file'),
        ('requirements.txt', 'Python requirements file'),
    ]
    
    files_ok = True
    for filepath, description in required_files:
        if not check_file_exists(filepath, description):
            files_ok = False
    
    print()
    
    # Check environment
    env_ok = check_environment()
    print()
    
    # Check Django setup
    django_ok = check_django_setup()
    print()
    
    # Check deployment readiness
    deploy_ok = check_deployment_readiness()
    print()
    
    # Summary
    print("="*60)
    print_status("Deployment Check Summary", "INFO")
    
    if files_ok and env_ok and django_ok and deploy_ok:
        print_status("🎉 Your Django deployment is ready!", "SUCCESS")
        print_status("Visit http://amirhoseainkhatami.ir to test your website", "INFO")
    else:
        print_status("⚠️ Some issues found in deployment setup", "WARNING")
        if not files_ok:
            print_status("- Fix missing files", "ERROR")
        if not env_ok:
            print_status("- Configure .env file", "ERROR")
        if not django_ok:
            print_status("- Fix Django configuration", "ERROR")
        if not deploy_ok:
            print_status("- Address deployment issues", "ERROR")
    
    return files_ok and env_ok and django_ok and deploy_ok

if __name__ == "__main__":
    try:
        success = main()
        if success:
            sys.exit(0)
        else:
            sys.exit(1)
    except KeyboardInterrupt:
        print_status("Deployment check cancelled by user", "WARNING")
        sys.exit(1)
    except Exception as e:
        print_status(f"Unexpected error: {e}", "ERROR")
        sys.exit(1) 