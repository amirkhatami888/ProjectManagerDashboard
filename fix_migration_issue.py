#!/usr/bin/env python
"""
Script to fix the migration issue where file_mime_type column already exists
but migration 0003_documentfile_file_mime_type is trying to add it again.
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

def fix_migration_issue():
    """Fix the migration issue by ensuring the problematic migration is marked as applied."""
    
    recorder = MigrationRecorder(connection)
    
    # Check if the migration is already recorded as applied
    migration_name = '0003_documentfile_file_mime_type'
    app_label = 'creator_subproject'
    
    # Check if migration is already applied
    applied = recorder.migration_qs.filter(
        app=app_label,
        name=migration_name
    ).exists()
    
    if not applied:
        print(f"Marking migration {app_label}.{migration_name} as applied...")
        recorder.record_applied(app_label, migration_name)
        print(f"Migration {app_label}.{migration_name} marked as applied successfully.")
    else:
        print(f"Migration {app_label}.{migration_name} is already marked as applied.")
    
    print("Migration issue fixed. You can now run 'python manage.py migrate' safely.")

if __name__ == '__main__':
    try:
        fix_migration_issue()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1) 