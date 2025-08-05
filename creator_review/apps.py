from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CreatorReviewConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "creator_review"
    verbose_name = _('Project Reviews')
    
    def ready(self):
        # Import signals
        import creator_review.signals
