from django.db import migrations


class Migration(migrations.Migration):
    """
    Restore automatic primary-key generation for project history rows.

    The deployed table was missing AUTO_INCREMENT even though Django models
    the id as a BigAutoField. Project saves then failed when the update-history
    signal attempted to insert a row.
    """

    dependencies = [
        ("creator_project", "0006_projectgalleryimage"),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                "ALTER TABLE `creator_project_projectupdatehistory` "
                "MODIFY `id` BIGINT NOT NULL AUTO_INCREMENT"
            ),
            reverse_sql=(
                "ALTER TABLE `creator_project_projectupdatehistory` "
                "MODIFY `id` BIGINT NOT NULL"
            ),
        ),
    ]
