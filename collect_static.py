#!/usr/bin/env python3
"""
Django Project Manager Dashboard - Static Files Collection Script
This script collects all static files for production deployment.
Execute this in your cPanel Python App interface.
"""

import os
import sys
import argparse
import shutil
from pathlib import Path

def print_status(message, status="INFO"):
    """Print formatted status message"""
    symbols = {
        "INFO": "ℹ️",
        "SUCCESS": "✅", 
        "ERROR": "❌",
        "WARNING": "⚠️"
    }
    print(f"{symbols.get(status, 'ℹ️')} {message}")

def sync_directory(source, destination, label):
    """Copy collected files into a web-server document-root directory."""
    source_path = Path(source)
    destination_path = Path(destination)

    if not source_path.exists():
        raise FileNotFoundError(f"{label} source directory does not exist: {source_path}")

    destination_path.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source_path, destination_path, dirs_exist_ok=True)
    print_status(f"{label} synchronized to {destination_path}", "SUCCESS")


def main(document_root=None):
    """Main static files collection function"""
    print_status("Django Project Manager Dashboard - Static Files Collection", "INFO")
    print("="*60)
    
    # Set Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project_dashboard.production_settings')

    try:
        import django
        from django.core.management import execute_from_command_line

        # Setup Django
        django.setup()
        print_status("Django environment configured", "SUCCESS")
        
        # Collect static files
        print_status("Collecting static files...", "INFO")
        execute_from_command_line(['manage.py', 'collectstatic', '--noinput'])
        print_status("Static files collected successfully!", "SUCCESS")

        if document_root:
            project_dir = Path(__file__).resolve().parent
            public_dir = Path(document_root).expanduser().resolve()
            sync_directory(project_dir / 'staticfiles', public_dir / 'static', 'Static files')
            sync_directory(project_dir / 'media', public_dir / 'media', 'Media files')
        else:
            print_status(
                "No document root supplied; static files remain in staticfiles/",
                "INFO",
            )

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
        parser = argparse.ArgumentParser(
            description="Collect Django static files and optionally publish them."
        )
        parser.add_argument(
            "--document-root",
            default=os.environ.get("DEPLOYMENT_DOCUMENT_ROOT"),
            help=(
                "Web document root for publishing /static and /media "
                "(or set DEPLOYMENT_DOCUMENT_ROOT)."
            ),
        )
        args = parser.parse_args()
        success = main(document_root=args.document_root)
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
