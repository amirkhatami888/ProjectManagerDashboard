from django.apps import AppConfig


class AiAssistantConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ai_assistant"
    verbose_name = "دستیار هوشمند"

    def ready(self):
        from .signals import connect_snapshot_signals
        connect_snapshot_signals()
