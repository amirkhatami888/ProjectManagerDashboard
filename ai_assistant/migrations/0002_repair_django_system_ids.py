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
        # MySQL refuses to alter a column participating in an FK (1832/1833).
        # Drop the affected standard Django constraints, widen both sides,
        # then recreate the constraints with the same names.
        cursor.execute("SET FOREIGN_KEY_CHECKS=0")
        try:
            foreign_keys = (
                ("activity_monitor_activitylog",
                 "activity_monitor_act_content_type_id_e50698bb_fk_django_co"),
                ("auth_permission",
                 "auth_permission_content_type_id_2f476e4b_fk_django_co"),
                ("django_admin_log",
                 "django_admin_log_content_type_id_c4bce8eb_fk_django_co"),
                ("accounts_user_user_permissions",
                 "accounts_user_user_p_permission_id_113bb443_fk_auth_perm"),
                ("auth_group_permissions",
                 "auth_group_permissio_permission_id_84c5c92e_fk_auth_perm"),
            )
            for table, constraint in foreign_keys:
                cursor.execute(
                    f"ALTER TABLE `{table}` DROP FOREIGN KEY `{constraint}`"
                )

            child_columns = (
                ("activity_monitor_activitylog", "content_type_id", "BIGINT NULL"),
                ("auth_permission", "content_type_id", "BIGINT NOT NULL"),
                ("django_admin_log", "content_type_id", "BIGINT NULL"),
                ("auth_group_permissions", "permission_id", "BIGINT NOT NULL"),
                ("accounts_user_user_permissions", "permission_id", "BIGINT NOT NULL"),
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

            constraints = (
                (
                    "activity_monitor_activitylog",
                    "activity_monitor_act_content_type_id_e50698bb_fk_django_co",
                    "content_type_id", "django_content_type", "id",
                ),
                (
                    "auth_permission",
                    "auth_permission_content_type_id_2f476e4b_fk_django_co",
                    "content_type_id", "django_content_type", "id",
                ),
                (
                    "django_admin_log",
                    "django_admin_log_content_type_id_c4bce8eb_fk_django_co",
                    "content_type_id", "django_content_type", "id",
                ),
                (
                    "accounts_user_user_permissions",
                    "accounts_user_user_p_permission_id_113bb443_fk_auth_perm",
                    "permission_id", "auth_permission", "id",
                ),
                (
                    "auth_group_permissions",
                    "auth_group_permissio_permission_id_84c5c92e_fk_auth_perm",
                    "permission_id", "auth_permission", "id",
                ),
            )
            for table, constraint, column, parent, parent_column in constraints:
                cursor.execute(
                    f"ALTER TABLE `{table}` ADD CONSTRAINT `{constraint}` "
                    f"FOREIGN KEY (`{column}`) REFERENCES `{parent}` (`{parent_column}`)"
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
