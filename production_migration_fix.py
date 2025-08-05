#!/usr/bin/env python
"""
Script to fix migration history on production server.
Run this on the production server to resolve the InconsistentMigrationHistory error.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project_dashboard.settings')
django.setup()

from django.db import connection

def fix_production_migration():
    """Fix the migration history on production server"""
    with connection.cursor() as cursor:
        try:
            # Check current migration state
            cursor.execute("SELECT app, name FROM django_migrations WHERE app = 'creator_subproject' ORDER BY id")
            migrations = cursor.fetchall()
            
            print("Current migrations in database:")
            for migration in migrations:
                print(f"  {migration[1]}")
            
            # Check if 0005_fix_executive_stage_migration is applied
            migration_0005_applied = any(m[1] == '0005_fix_executive_stage_migration' for m in migrations)
            print(f"\n0005_fix_executive_stage_migration applied: {migration_0005_applied}")
            
            # Check if 0006_merge_20250805_1122 is applied
            migration_0006_applied = any(m[1] == '0006_merge_20250805_1122' for m in migrations)
            print(f"0006_merge_20250805_1122 applied: {migration_0006_applied}")
            
            # If merge migration is applied but the dependency is not, we need to add the dependency
            if migration_0006_applied and not migration_0005_applied:
                print("\nFixing migration history...")
                
                # Add the missing dependency migration
                cursor.execute("""
                    INSERT INTO django_migrations (app, name, applied) 
                    VALUES ('creator_subproject', '0005_fix_executive_stage_migration', datetime('now'))
                """)
                
                print("✅ Added missing migration: 0005_fix_executive_stage_migration")
                print("✅ Migration history is now consistent")
            else:
                print("\nMigration history appears to be consistent")
                
        except Exception as e:
            print(f"❌ Error fixing migration: {str(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    fix_production_migration() 