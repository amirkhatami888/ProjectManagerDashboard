#!/usr/bin/env python
import os
import sys
import django
import sqlite3

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project_dashboard.settings')
django.setup()

def apply_migration_manually():
    """Manually apply the migration to add program_opening_date column"""
    db_path = 'db.sqlite3'
    
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found!")
        return
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the column already exists
        cursor.execute("PRAGMA table_info(creator_program_program)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'program_opening_date' in column_names:
            print("Column 'program_opening_date' already exists!")
            return
        
        # Add the column
        cursor.execute("""
            ALTER TABLE creator_program_program 
            ADD COLUMN program_opening_date DATE NULL
        """)
        
        # Commit the changes
        conn.commit()
        print("Successfully added 'program_opening_date' column to creator_program_program table!")
        
        # Update the migration record
        cursor.execute("""
            INSERT INTO django_migrations (app, name, applied) 
            VALUES ('creator_program', '0005_program_opening_date', datetime('now'))
        """)
        conn.commit()
        print("Migration record added to django_migrations table!")
        
    except Exception as e:
        print(f"Error applying migration: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    apply_migration_manually() 