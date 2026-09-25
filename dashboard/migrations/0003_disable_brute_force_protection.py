from django.db import migrations, models


def disable_existing_brute_force_protection(apps, schema_editor):
    SecuritySettings = apps.get_model('dashboard', 'SecuritySettings')
    SecuritySettings.objects.update(brute_force_enabled=False)


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0002_securitysettings_brute_force_enabled'),
    ]

    operations = [
        migrations.AlterField(
            model_name='securitysettings',
            name='brute_force_enabled',
            field=models.BooleanField(default=False, verbose_name='Brute Force Protection enabled'),
        ),
        migrations.RunPython(
            disable_existing_brute_force_protection,
            migrations.RunPython.noop,
        ),
    ]
