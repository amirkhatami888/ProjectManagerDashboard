#!/usr/bin/env python
"""
Script to reset migration state for all apps that depend on creator_subproject
to fix the migration dependency issue.
"""

import os
import sys
import django
from django.core.management import execute_from_command_line
from django.db import connection

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project_dashboard.settings')
django.setup()

from django.db.migrations.recorder import MigrationRecorder

def reset_all_migrations():
    """Reset migration state for all dependent apps."""
    
    recorder = MigrationRecorder(connection)
    
    # List of apps to reset (apps that depend on creator_subproject)
    apps_to_reset = [
        'creator_subproject',
        'creator_review',
        'creator_project',
        'notifications',
        'notifications_sms',
        'webhooks',
        'reporter'
    ]
    
    for app_label in apps_to_reset:
        # Remove all migration records for this app
        deleted_count = recorder.migration_qs.filter(app=app_label).delete()[0]
        print(f"Reset migration state for {app_label} (deleted {deleted_count} records)")
    
    print("\nMigration state reset complete.")
    print("Now you can run: python manage.py migrate")

if __name__ == '__main__':
    try:
        reset_all_migrations()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1) 