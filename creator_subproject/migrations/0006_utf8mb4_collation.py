from django.db import migrations


class Migration(migrations.Migration):
    """
    Migration to set UTF8MB4 Unicode collation for all text fields.
    This ensures proper support for Persian/Farsi text and emojis.
    """
    
    dependencies = [
        ('creator_subproject', '0005_auto_20250805_0925'),
    ]

    def set_utf8mb4_collation(apps, schema_editor):
        """
        Set UTF8MB4 collation for all text fields in the database.
        This is a data migration that runs SQL commands.
        """
        if schema_editor.connection.vendor == 'mysql':
            # Get all tables for this app
            tables = [
                'creator_subproject_subproject',
                'creator_subproject_allocation',
                'creator_subproject_financialdocument',
                'creator_subproject_payment',
                'creator_subproject_situationreport',
                'creator_subproject_subprojectgalleryimage',
                'creator_subproject_documentfile',
            ]
            
            for table in tables:
                # Convert table to UTF8MB4
                schema_editor.execute(
                    f"ALTER TABLE `{table}` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )
                
                # Update specific text columns to ensure proper collation
                schema_editor.execute(f"""
                    ALTER TABLE `{table}` 
                    MODIFY COLUMN `name` VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
                    MODIFY COLUMN `description` TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
                """)

    def reverse_set_utf8mb4_collation(apps, schema_editor):
        """
        Reverse migration - convert back to utf8 (if needed).
        """
        if schema_editor.connection.vendor == 'mysql':
            tables = [
                'creator_subproject_subproject',
                'creator_subproject_allocation',
                'creator_subproject_financialdocument',
                'creator_subproject_payment',
                'creator_subproject_situationreport',
                'creator_subproject_subprojectgalleryimage',
                'creator_subproject_documentfile',
            ]
            
            for table in tables:
                schema_editor.execute(
                    f"ALTER TABLE `{table}` CONVERT TO CHARACTER SET utf8 COLLATE utf8_unicode_ci"
                )

    operations = [
        migrations.RunPython(
            set_utf8mb4_collation,
            reverse_set_utf8mb4_collation,
        ),
    ] 