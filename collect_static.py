#!/usr/bin/env python3
"""
Django Project Manager Dashboard - Static Files Collection Script
This script collects all static files for production deployment.
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
    """Main static files collection function"""
    print_status("Django Project Manager Dashboard - Static Files Collection", "INFO")
    print("="*60)
    
    # Set Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project_dashboard.production_settings')
    
    try:
        # Setup Django
        django.setup()
        print_status("Django environment configured", "SUCCESS")
        
        # Collect static files
        print_status("Collecting static files...", "INFO")
        execute_from_command_line(['manage.py', 'collectstatic', '--noinput'])
        print_status("Static files collected successfully!", "SUCCESS")
        
        # Show information
        print()
        print_status("Static files collection completed!", "SUCCESS")
        print_status("Static files are now ready for production", "INFO")
        print("Your CSS, JavaScript, and image files should now load correctly on your website.")
        
        return True
        
    except Exception as e:
        print_status(f"Error during static files collection: {e}", "ERROR")
        print_status("Make sure your .env file is configured correctly", "WARNING")
        return False

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print_status("🎉 Static files collection completed successfully!", "SUCCESS")
            sys.exit(0)
        else:
            print_status("❌ Static files collection failed", "ERROR")
            sys.exit(1)
    except KeyboardInterrupt:
        print_status("Static files collection cancelled by user", "WARNING")
        sys.exit(1)
    except Exception as e:
        print_status(f"Unexpected error: {e}", "ERROR")
        sys.exit(1) 