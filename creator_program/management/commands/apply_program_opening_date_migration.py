from django.core.management.base import BaseCommand
import sqlite3
import os


class Command(BaseCommand):
    help = 'Manually apply the migration to add program_opening_date column'

    def handle(self, *args, **options):
        db_path = 'db.sqlite3'
        
        if not os.path.exists(db_path):
            self.stdout.write(
                self.style.ERROR(f"Database file {db_path} not found!")
            )
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
                self.stdout.write(
                    self.style.WARNING("Column 'program_opening_date' already exists!")
                )
                return
            
            # Add the column
            cursor.execute("""
                ALTER TABLE creator_program_program 
                ADD COLUMN program_opening_date DATE NULL
            """)
            
            # Commit the changes
            conn.commit()
            self.stdout.write(
                self.style.SUCCESS("Successfully added 'program_opening_date' column to creator_program_program table!")
            )
            
            # Update the migration record
            cursor.execute("""
                INSERT INTO django_migrations (app, name, applied) 
                VALUES ('creator_program', '0005_program_opening_date', datetime('now'))
            """)
            conn.commit()
            self.stdout.write(
                self.style.SUCCESS("Migration record added to django_migrations table!")
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error applying migration: {e}")
            )
        finally:
            conn.close() 