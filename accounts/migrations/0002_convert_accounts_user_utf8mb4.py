# Fix accounts_user table charset so province accepts Persian/UTF-8 (DataError 1366)

from django.db import migrations


def convert_utf8mb4(apps, schema_editor):
    """Convert accounts_user table to utf8mb4 so province and other text columns accept Persian."""
    if schema_editor.connection.vendor != "mysql":
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            "ALTER TABLE accounts_user CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(convert_utf8mb4, migrations.RunPython.noop),
    ]
