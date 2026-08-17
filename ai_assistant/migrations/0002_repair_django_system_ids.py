from django.db import migrations


def repair_system_auto_increment_ids(apps, schema_editor):
    """Repair legacy MySQL tables imported without AUTO_INCREMENT on id.

    The project has historically used a MariaDB/MySQL schema whose integer
    primary keys were sometimes created without their auto-increment flag.
    Django's post_migrate signal uses bulk inserts for content types and
    permissions, which exposes that inconsistency.
    """
    connection = schema_editor.connection
    if connection.vendor != "mysql":
        return

    tables = (
        "django_migrations",
        "django_content_type",
        "auth_permission",
        "django_admin_log",
    )
    with connection.cursor() as cursor:
        for table in tables:
            cursor.execute(
                f"ALTER TABLE `{table}` "
                "MODIFY `id` BIGINT NOT NULL AUTO_INCREMENT"
            )


class Migration(migrations.Migration):
    dependencies = [
        ("ai_assistant", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            repair_system_auto_increment_ids,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
