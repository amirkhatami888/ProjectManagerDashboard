#!/usr/bin/env python
"""
Script to specifically fix the file_mime_type migration issue.
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

def check_column_exists(table_name, column_name):
    """Check if a column exists in a table."""
    with connection.cursor() as cursor:
        if connection.vendor == 'sqlite':
            cursor.execute("PRAGMA table_info(%s)" % table_name)
            columns = cursor.fetchall()
            return any(col[1] == column_name for col in columns)
        elif connection.vendor == 'mysql':
            cursor.execute("""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = %s AND COLUMN_NAME = %s
            """, [table_name, column_name])
            return cursor.fetchone()[0] > 0
        else:
            # For other databases, try a generic approach
            try:
                cursor.execute("SELECT %s FROM %s LIMIT 1" % (column_name, table_name))
                return True
            except:
                return False

def fix_file_mime_type_migration():
    """Fix the file_mime_type migration issue."""
    
    recorder = MigrationRecorder(connection)
    
    # Check if the file_mime_type column already exists
    table_name = 'creator_subproject_documentfile'
    column_name = 'file_mime_type'
    
    if check_column_exists(table_name, column_name):
        print(f"Column {column_name} already exists in table {table_name}")
        
        # Mark the problematic migration as applied
        migration_name = '0003_documentfile_file_mime_type'
        app_label = 'creator_subproject'
        
        if not recorder.migration_qs.filter(app=app_label, name=migration_name).exists():
            recorder.record_applied(app_label, migration_name)
            print(f"Marked {app_label}.{migration_name} as applied")
        else:
            print(f"Migration {app_label}.{migration_name} is already marked as applied")
        
        print("File MIME type migration issue fixed.")
    else:
        print(f"Column {column_name} does not exist in table {table_name}")
        print("This suggests the migration should run normally.")

if __name__ == '__main__':
    try:
        fix_file_mime_type_migration()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1) 