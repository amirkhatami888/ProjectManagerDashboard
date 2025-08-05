from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Fix migration history for creator_subproject app'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            try:
                # Check current migration state
                cursor.execute("SELECT app, name FROM django_migrations WHERE app = 'creator_subproject' ORDER BY id")
                migrations = cursor.fetchall()
                
                self.stdout.write("Current migrations in database:")
                for migration in migrations:
                    self.stdout.write(f"  {migration[1]}")
                
                # Check if 0005_fix_executive_stage_migration is applied
                migration_0005_applied = any(m[1] == '0005_fix_executive_stage_migration' for m in migrations)
                self.stdout.write(f"\n0005_fix_executive_stage_migration applied: {migration_0005_applied}")
                
                # Check if 0006_merge_20250805_1122 is applied
                migration_0006_applied = any(m[1] == '0006_merge_20250805_1122' for m in migrations)
                self.stdout.write(f"0006_merge_20250805_1122 applied: {migration_0006_applied}")
                
                # If merge migration is applied but the dependency is not, we need to add the dependency
                if migration_0006_applied and not migration_0005_applied:
                    self.stdout.write("\nFixing migration history...")
                    
                    # Add the missing dependency migration
                    cursor.execute("""
                        INSERT INTO django_migrations (app, name, applied) 
                        VALUES ('creator_subproject', '0005_fix_executive_stage_migration', datetime('now'))
                    """)
                    
                    self.stdout.write(
                        self.style.SUCCESS("✅ Added missing migration: 0005_fix_executive_stage_migration")
                    )
                    self.stdout.write(
                        self.style.SUCCESS("✅ Migration history is now consistent")
                    )
                else:
                    self.stdout.write("\nMigration history appears to be consistent")
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"❌ Error fixing migration: {str(e)}")
                )
                import traceback
                self.stdout.write(f"Traceback: {traceback.format_exc()}") 