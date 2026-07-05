from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import ProjectReview


@receiver(post_save, sender=ProjectReview)
def send_sms_on_project_rejection(sender, instance, created, **kwargs):
    return
