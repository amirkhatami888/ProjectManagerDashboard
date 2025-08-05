#!/usr/bin/env python
"""
Script to fix the migration dependency issue between creator_review and creator_subproject.
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

def fix_migration_dependency():
    """Fix the migration dependency issue."""
    
    recorder = MigrationRecorder(connection)
    
    # Remove the problematic migration records
    print("Removing migration records for creator_review and creator_subproject...")
    recorder.migration_qs.filter(app='creator_review').delete()
    recorder.migration_qs.filter(app='creator_subproject').delete()
    
    print("Migration records removed. Now marking them as applied in correct order...")
    
    # Mark them as applied in the correct dependency order
    # First, mark creator_subproject.0001_initial
    recorder.record_applied('creator_subproject', '0001_initial')
    print("Marked creator_subproject.0001_initial as applied")
    
    # Then mark creator_review.0001_initial
    recorder.record_applied('creator_review', '0001_initial')
    print("Marked creator_review.0001_initial as applied")
    
    # Mark the remaining creator_subproject migrations
    remaining_subproject_migrations = [
        '0003_documentfile_file_mime_type',
        '0004_remove_executive_stage_field', 
        '0005_auto_20250805_0925',
        '0006_merge_20250805_1122'
    ]
    
    for migration_name in remaining_subproject_migrations:
        recorder.record_applied('creator_subproject', migration_name)
        print(f"Marked creator_subproject.{migration_name} as applied")
    
    print("Migration dependency issue should be resolved.")

if __name__ == '__main__':
    try:
        fix_migration_dependency()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1) 