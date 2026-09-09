from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("ai_assistant", "0004_stage2_settings_usage"),
        ("creator_project", "0001_initial"),
        ("creator_subproject", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AIKnowledgeEntry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200)), ("category", models.CharField(default="general", max_length=60)),
                ("content", models.TextField()), ("source", models.CharField(blank=True, default="سامانه داخلی", max_length=300)),
                ("is_active", models.BooleanField(default=True)), ("priority", models.PositiveIntegerField(default=50)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ], options={"ordering": ["-priority", "title"]},
        ),
        migrations.CreateModel(
            name="AIAutomationRule",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=160)), ("description", models.TextField(blank=True, default="")),
                ("rule_type", models.CharField(default="project_health", max_length=50)), ("config", models.JSONField(blank=True, default=dict)),
                ("is_active", models.BooleanField(default=True)), ("last_run_at", models.DateTimeField(blank=True, null=True)),
                ("last_result", models.JSONField(blank=True, default=dict)), ("created_at", models.DateTimeField(auto_now_add=True)),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ], options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="AIExpertComment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("content", models.TextField()), ("severity", models.CharField(default="مهم", max_length=20)),
                ("status", models.CharField(default="draft", max_length=20)), ("evidence", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)), ("published_at", models.DateTimeField(blank=True, null=True)),
                ("author", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="ai_expert_comments", to=settings.AUTH_USER_MODEL)),
                ("project", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="ai_expert_comments", to="creator_project.project")),
                ("subproject", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="ai_expert_comments", to="creator_subproject.subproject")),
            ], options={"ordering": ["-created_at"]},
        ),
    ]
