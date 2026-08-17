from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("ai_assistant", "0003_aipendingaction"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="aiuserpolicy",
            name="api_key_encrypted",
            field=models.TextField(blank=True, default="", editable=False),
        ),
        migrations.CreateModel(
            name="AIPlatformSettings",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("enabled", models.BooleanField(default=True, verbose_name="فعال")),
                ("provider_name", models.CharField(default="gapgpt", max_length=50)),
                ("provider_endpoint", models.URLField(blank=True, default="")),
                ("provider_model", models.CharField(default="default", max_length=120)),
                ("gapgpt_api_key_encrypted", models.TextField(blank=True, default="", editable=False)),
                ("tavily_api_key_encrypted", models.TextField(blank=True, default="", editable=False)),
                ("request_timeout_seconds", models.PositiveIntegerField(default=60)),
                ("daily_request_limit", models.PositiveIntegerField(default=1000)),
                ("monthly_request_limit", models.PositiveIntegerField(default=20000)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"verbose_name": "تنظیمات سراسری دستیار", "verbose_name_plural": "تنظیمات سراسری دستیار"},
        ),
        migrations.CreateModel(
            name="AIRolePolicy",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("role", models.CharField(max_length=30, unique=True)),
                ("is_enabled", models.BooleanField(default=True)),
                ("daily_message_limit", models.PositiveIntegerField(default=30)),
                ("monthly_message_limit", models.PositiveIntegerField(default=500)),
                ("allow_web_search", models.BooleanField(default=True)),
                ("allow_write_actions", models.BooleanField(default=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"verbose_name": "سیاست نقش دستیار", "verbose_name_plural": "سیاست‌های نقش دستیار"},
        ),
        migrations.CreateModel(
            name="AIUsageRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("provider", models.CharField(max_length=50)),
                ("request_count", models.PositiveIntegerField(default=1)),
                ("input_tokens", models.PositiveIntegerField(default=0)),
                ("output_tokens", models.PositiveIntegerField(default=0)),
                ("search_credits", models.PositiveIntegerField(default=0)),
                ("latency_ms", models.PositiveIntegerField(default=0)),
                ("status", models.CharField(default="success", max_length=20)),
                ("error_code", models.CharField(blank=True, default="", max_length=100)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="ai_usage_records", to=settings.AUTH_USER_MODEL)),
            ],
            options={"verbose_name": "مصرف دستیار", "verbose_name_plural": "مصرف دستیار", "ordering": ["-created_at"]},
        ),
    ]
