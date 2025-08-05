#!/usr/bin/env python
"""
Script to reset migration state for creator_subproject app
to fix the migration issue with file_mime_type field.
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

def reset_migrations():
    """Reset migration state for creator_subproject app."""
    
    recorder = MigrationRecorder(connection)
    app_label = 'creator_subproject'
    
    # Remove all migration records for this app
    recorder.migration_qs.filter(app=app_label).delete()
    
    print(f"Reset migration state for {app_label}")
    print("Now you can run: python manage.py migrate creator_subproject")

if __name__ == '__main__':
    try:
        reset_migrations()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1) 