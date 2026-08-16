from django.db import migrations


class Migration(migrations.Migration):
    """
    Restore the auto-generated primary key on the live subproject table.

    The Django model uses the app's default BigAutoField, but the deployed
    MySQL table had an id column without AUTO_INCREMENT. New subprojects then
    failed with MySQL error 1364.
    """

    dependencies = [
        ("creator_subproject", "0007_remove_gallery_model"),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                "ALTER TABLE `creator_subproject_subproject` "
                "MODIFY `id` BIGINT NOT NULL AUTO_INCREMENT"
            ),
            reverse_sql=(
                "ALTER TABLE `creator_subproject_subproject` "
                "MODIFY `id` BIGINT NOT NULL"
            ),
        ),
    ]
