from django.db import migrations


class Migration(migrations.Migration):
    """
    Restore automatic primary-key generation for gallery image rows.

    The deployed table was missing AUTO_INCREMENT even though Django models
    the id as a BigAutoField. Image saves then failed when attempting to insert a row.
    """

    dependencies = [
        ("creator_project", "0007_restore_project_history_id_autoincrement"),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                "ALTER TABLE `creator_project_projectgalleryimage` "
                "MODIFY `id` BIGINT NOT NULL AUTO_INCREMENT"
            ),
            reverse_sql=(
                "ALTER TABLE `creator_project_projectgalleryimage` "
                "MODIFY `id` BIGINT NOT NULL"
            ),
        ),
    ]