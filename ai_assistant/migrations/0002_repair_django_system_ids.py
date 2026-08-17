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

    with connection.cursor() as cursor:
        # MySQL refuses to alter a referenced PK (1833).  These are Django's
        # standard FK columns in this project.  Widen the child columns first,
        # then the parent columns, while checks are disabled for this brief
        # schema-only operation.  FK definitions remain in place.
        cursor.execute("SET FOREIGN_KEY_CHECKS=0")
        try:
            child_columns = (
                ("activity_monitor_activitylog", "content_type_id", "BIGINT NULL"),
                ("auth_permission", "content_type_id", "BIGINT NOT NULL"),
                ("django_admin_log", "content_type_id", "BIGINT NULL"),
                ("auth_group_permissions", "permission_id", "BIGINT NOT NULL"),
                ("auth_user_user_permissions", "permission_id", "BIGINT NOT NULL"),
            )
            for table, column, definition in child_columns:
                cursor.execute(
                    f"ALTER TABLE `{table}` MODIFY `{column}` {definition}"
                )

            parent_tables = (
                "django_migrations",
                "django_content_type",
                "auth_permission",
                "django_admin_log",
            )
            for table in parent_tables:
                cursor.execute(
                    f"ALTER TABLE `{table}` "
                    "MODIFY `id` BIGINT NOT NULL AUTO_INCREMENT"
                )
        finally:
            cursor.execute("SET FOREIGN_KEY_CHECKS=1")


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
