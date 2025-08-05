from django.core.management.base import BaseCommand
from django.db import connection
from django.apps import apps


class Command(BaseCommand):
    help = 'Set up UTF8MB4 Unicode collation for all database tables'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Setting up UTF8MB4 Unicode collation...')
        )
        
        try:
            with connection.cursor() as cursor:
                # Get all table names
                cursor.execute("SHOW TABLES")
                tables = cursor.fetchall()
                
                for table in tables:
                    table_name = table[0]
                    self.stdout.write(f"Processing table: {table_name}")
                    
                    # Convert table to UTF8MB4
                    try:
                        cursor.execute(f"""
                            ALTER TABLE `{table_name}` 
                            CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
                        """)
                        self.stdout.write(
                            self.style.SUCCESS(f"✓ Converted {table_name} to UTF8MB4")
                        )
                    except Exception as e:
                        self.stdout.write(
                            self.style.WARNING(f"⚠ Could not convert {table_name}: {e}")
                        )
                
                # Set default character set for the database
                cursor.execute("""
                    ALTER DATABASE `{}` 
                    CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
                """.format(connection.settings_dict['NAME']))
                
                self.stdout.write(
                    self.style.SUCCESS('✓ Database default character set updated')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error setting up UTF8MB4 collation: {e}')
            )
            return
        
        self.stdout.write(
            self.style.SUCCESS('✓ UTF8MB4 Unicode collation setup completed successfully!')
        ) 