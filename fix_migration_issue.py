#!/usr/bin/env python
"""
Script to fix the migration issue with duplicate image_mime_type column.
This script will manually update the Django migrations table to resolve the conflict.
"""

import os
import sys
import django
import sqlite3

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project_dashboard.settings')
django.setup()

def fix_migration_issue():
    """Fix the migration issue by updating the migrations table"""
    db_path = 'db.sqlite3'
    
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found!")
        return
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the migration record already exists
        cursor.execute("""
            SELECT * FROM django_migrations 
            WHERE app = 'creator_subproject' 
            AND name = '0002_subprojectgalleryimage_image_mime_type_and_more'
        """)
        
        if cursor.fetchone():
            print("Migration record already exists in django_migrations table!")
            return
        
        # Add the migration record to mark it as applied
        cursor.execute("""
            INSERT INTO django_migrations (app, name, applied) 
            VALUES ('creator_subproject', '0002_subprojectgalleryimage_image_mime_type_and_more', datetime('now'))
        """)
        
        # Commit the changes
        conn.commit()
        print("Successfully added migration record to django_migrations table!")
        print("The migration conflict has been resolved.")
        
    except Exception as e:
        print(f"Error fixing migration: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    fix_migration_issue()