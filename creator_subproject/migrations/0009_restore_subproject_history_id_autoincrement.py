from django.db import migrations


class Migration(migrations.Migration):
    """
    Restore automatic primary-key generation for subproject history rows.
    """

    dependencies = [
        ("creator_subproject", "0008_restore_subproject_id_autoincrement"),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                "ALTER TABLE `creator_subproject_subprojectupdatehistory` "
                "MODIFY `id` BIGINT NOT NULL AUTO_INCREMENT"
            ),
            reverse_sql=(
                "ALTER TABLE `creator_subproject_subprojectupdatehistory` "
                "MODIFY `id` BIGINT NOT NULL"
            ),
        ),
    ]
