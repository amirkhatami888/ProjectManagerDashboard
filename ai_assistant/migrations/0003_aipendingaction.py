from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):
    dependencies = [
        ("ai_assistant", "0002_repair_django_system_ids"),
    ]

    operations = [
        migrations.CreateModel(
            name="AIPendingAction",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("action_type", models.CharField(default="update_field", max_length=40)),
                ("payload", models.JSONField(default=dict)),
                ("status", models.CharField(default="pending", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("expires_at", models.DateTimeField()),
                ("confirmed_at", models.DateTimeField(blank=True, null=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="ai_pending_actions", to=settings.AUTH_USER_MODEL, verbose_name="کاربر")),
            ],
            options={
                "verbose_name": "عملیات در انتظار تأیید AI",
                "verbose_name_plural": "عملیات در انتظار تأیید AI",
                "ordering": ["-created_at"],
            },
        ),
    ]
