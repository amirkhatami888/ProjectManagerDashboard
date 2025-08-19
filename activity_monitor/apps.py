from django.apps import AppConfig


class ActivityMonitorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'activity_monitor'
    verbose_name = 'Activity Monitor'
    
    def ready(self):
        """Initialize the app when Django starts"""
        import activity_monitor.signals
