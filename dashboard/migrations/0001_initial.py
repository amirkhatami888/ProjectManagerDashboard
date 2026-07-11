# Generated manually for dashboard security settings

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='SecuritySettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('turnstile_enabled', models.BooleanField(default=True, verbose_name='Cloudflare Turnstile enabled')),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Security settings',
                'verbose_name_plural': 'Security settings',
            },
        ),
    ]
