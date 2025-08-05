#!/usr/bin/env python3
"""
Django Project Manager Dashboard - Superuser Creation Script
This script creates a superuser for accessing Django admin.
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

def main():
    """Main superuser creation function"""
    print_status("Django Project Manager Dashboard - Superuser Creation", "INFO")
    print("="*60)
    
    # Set Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project_dashboard.production_settings')
    
    try:
        # Setup Django
        django.setup()
        print_status("Django environment configured", "SUCCESS")
        
        # Create superuser interactively
        print_status("Creating superuser account...", "INFO")
        print("Please provide the following information for your admin account:")
        print()
        
        execute_from_command_line(['manage.py', 'createsuperuser'])
        
        print()
        print_status("Superuser created successfully!", "SUCCESS")
        print_status("You can now access the admin panel at: http://amirhoseainkhatami.ir/admin/", "INFO")
        print_status("Use the username and password you just created to log in", "INFO")
        
        return True
        
    except Exception as e:
        print_status(f"Error during superuser creation: {e}", "ERROR")
        print_status("Make sure your database is set up correctly", "WARNING")
        return False

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print_status("🎉 Superuser creation completed successfully!", "SUCCESS")
            sys.exit(0)
        else:
            print_status("❌ Superuser creation failed", "ERROR")
            sys.exit(1)
    except KeyboardInterrupt:
        print_status("Superuser creation cancelled by user", "WARNING")
        sys.exit(1)
    except Exception as e:
        print_status(f"Unexpected error: {e}", "ERROR")
        sys.exit(1) 