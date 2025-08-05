#!/usr/bin/env python
"""
Script to mark all existing migrations as applied without running them,
since the database tables already exist but migration records were deleted.
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
from django.db.migrations.loader import MigrationLoader

def mark_migrations_applied():
    """Mark all existing migrations as applied without running them."""
    
    recorder = MigrationRecorder(connection)
    
    # Get the migration loader to find all migrations
    loader = MigrationLoader(connection)
    
    # List of apps to process
    apps_to_process = [
        'accounts',
        'admin', 
        'auth',
        'contenttypes',
        'creator_program',
        'creator_project',
        'creator_review', 
        'creator_subproject',
        'notifications',
        'notifications_sms',
        'reporter',
        'sessions',
        'webhooks'
    ]
    
    total_marked = 0
    
    for app_label in apps_to_process:
        if app_label in loader.migrated_apps:
            # Get all migrations for this app
            app_migrations = loader.graph.nodes.get(app_label, {})
            
            for migration_name in app_migrations:
                # Check if already applied
                if not recorder.migration_qs.filter(app=app_label, name=migration_name).exists():
                    recorder.record_applied(app_label, migration_name)
                    print(f"Marked {app_label}.{migration_name} as applied")
                    total_marked += 1
    
    print(f"\nTotal migrations marked as applied: {total_marked}")
    print("Migration state is now consistent with the database.")

if __name__ == '__main__':
    try:
        mark_migrations_applied()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1) 