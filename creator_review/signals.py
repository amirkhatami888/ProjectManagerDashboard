from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

from .models import ProjectReview
from notifications_sms.utils import IPPanelSMSSender, format_project_rejected_message

@receiver(post_save, sender=ProjectReview)
def send_sms_on_project_rejection(sender, instance, created, **kwargs):
    """
    Send SMS notification when a project is rejected by an expert
    """
    # Only send on update (not create) and when status is REJECTED
    if not created and instance.status == 'REJECTED' and instance.rejection_reason:
        # Get the project
        project = instance.project
        
        # Get the project creator/owner
        creator = project.created_by
        
        # Skip if creator has no phone number
        if not creator or not creator.phone_number:
            return
        
        # Format the message with the rejection reason
        message = format_project_rejected_message(instance.rejection_reason)
        
        # Send SMS
        IPPanelSMSSender.send_sms(
            creator.phone_number,
            message,
            sender_user=instance.expert,
            recipient_user=creator
        ) 