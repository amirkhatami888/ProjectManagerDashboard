from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q
from django.conf import settings
from django.db import transaction
import logging
import datetime

from creator_project.models import Project, ProjectRejectionComment
from accounts.models import User
from notifications.models import RejectionSMSSettings, SMSLog, ProjectExpertNotification
from utils.ippanel import IPPanelClient

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Sends SMS notifications for rejected projects'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting rejection SMS notification check...'))
        
        # Get SMS settings
        sms_settings = RejectionSMSSettings.get_settings()
        
        if not sms_settings.enabled:
            self.stdout.write(self.style.WARNING('Rejection SMS notifications are disabled in settings'))
            return
        
        # Get current date and calculate the threshold date (last 24 hours)
        now = timezone.now()
        threshold_date = now - datetime.timedelta(days=1)
        
        # Find recent rejection comments
        rejection_comments = ProjectRejectionComment.objects.filter(
            created_at__gte=threshold_date,
            is_resolved=False
        )
        
        self.stdout.write(f'Found {rejection_comments.count()} recent rejection comments')
        
        # Group comments by project and creator
        for comment in rejection_comments:
            project = comment.project
            project_creator = project.created_by
            
            # Skip if creator has no phone number
            if not project_creator.phone_number:
                self.stdout.write(self.style.WARNING(f'No phone number for user {project_creator.username}'))
                continue
            
            # Check if already notified for this comment
            existing_notification = ProjectExpertNotification.objects.filter(
                project=project,
                expert=project_creator,
                notification_type='project_rejection',
                created_at__gte=threshold_date
            ).exists()
            
            if existing_notification:
                self.stdout.write(self.style.WARNING(f'User {project_creator.username} already notified for project {project.name}'))
                continue
            
            # Send the rejection SMS
            self._send_rejection_sms(project_creator, project, comment, sms_settings)
            
            # Create notification record
            ProjectExpertNotification.objects.create(
                project=project,
                expert=project_creator,
                notification_type='project_rejection',
                notified_via_sms=True,
                rejection_reason=comment.comment
            )
        
        # Update last run timestamp
        sms_settings.last_run = now
        sms_settings.save()
        
        self.stdout.write(self.style.SUCCESS('Rejection SMS notification check completed'))
    
    def _send_rejection_sms(self, user, project, comment, sms_settings):
        """Send SMS notification for a rejected project"""
        try:
            # Format the message
            message = sms_settings.message_template.format(
                project_name=project.name,
                rejection_reason=comment.comment
            )
            
            # Create SMS log entry
            sms_log = SMSLog.objects.create(
                recipient=user,
                message=message,
                project_name=project.name,
                project_id=project.project_id,
                province=project.province,
                status='pending'
            )
            
            # Get general SMS settings for API key and sender number
            general_settings = SMSSettings.get_settings()
            
            # Initialize SMS client
            sms_client = IPPanelClient(api_key=general_settings.api_key)
            
            # Send SMS
            result = sms_client.send_sms(
                recipient_numbers=user.phone_number,
                message_text=message,
                sender_number=general_settings.sender_number
            )
            
            with transaction.atomic():
                if result.get('meta', {}).get('status') == True:
                    # Update log with success
                    message_id = result.get('data', {}).get('message_id')
                    sms_log.status = 'sent'
                    sms_log.message_id = message_id
                    self.stdout.write(self.style.SUCCESS(
                        f'Rejection SMS sent to {user.username} ({user.phone_number}) for project {project.name}'
                    ))
                else:
                    # Update log with error
                    error_message = result.get('meta', {}).get('message', 'Unknown error')
                    sms_log.status = 'failed'
                    sms_log.error_message = error_message
                    self.stdout.write(self.style.ERROR(
                        f'Failed to send rejection SMS to {user.username}: {error_message}'
                    ))
                
                sms_log.save()
                
        except Exception as e:
            logger.error(f"Error sending rejection SMS for project {project.name}: {str(e)}")
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}')) 