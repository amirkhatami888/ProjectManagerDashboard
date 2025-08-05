#!/usr/bin/env python
"""
Script to fix the migration issue where file_mime_type field already exists
but migration 0003 is trying to add it again.
"""

import os
import sys
import django
from django.conf import settings

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project_dashboard.settings')
django.setup()

from django.db import connection
from django.db.migrations.recorder import MigrationRecorder

def fix_migration_issue():
    """Mark the problematic migration as applied without running it."""
    
    # Check if the migration is already recorded as applied
    recorder = MigrationRecorder(connection)
    
    # Check if the migration is already in the database
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*) FROM django_migrations 
            WHERE app = 'creator_subproject' AND name = '0003_documentfile_file_mime_type'
        """)
        count = cursor.fetchone()[0]
        
        if count == 0:
            print("Migration 0003_documentfile_file_mime_type is not applied yet.")
            print("Adding it to the migration history without running the operations...")
            
            # Insert the migration record without running the operations
            cursor.execute("""
                INSERT INTO django_migrations (app, name, applied) 
                VALUES ('creator_subproject', '0003_documentfile_file_mime_type', datetime('now'))
            """)
            
            print("✓ Migration 0003_documentfile_file_mime_type marked as applied.")
        else:
            print("✓ Migration 0003_documentfile_file_mime_type is already applied.")
    
    # Check if the file_mime_type column actually exists (SQLite syntax)
    with connection.cursor() as cursor:
        cursor.execute("PRAGMA table_info(creator_subproject_documentfile)")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]
        
        if 'file_mime_type' in column_names:
            print("✓ file_mime_type column exists in the database.")
        else:
            print("⚠ file_mime_type column does not exist in the database.")
            print("This might indicate a different issue.")

if __name__ == "__main__":
    print("Fixing migration issue for creator_subproject.0003_documentfile_file_mime_type...")
    fix_migration_issue()
    print("Done!")