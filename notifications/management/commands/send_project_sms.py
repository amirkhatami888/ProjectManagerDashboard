from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q
from django.conf import settings
from django.db import transaction
import logging
import datetime

from creator_project.models import Project, ProjectRejectionComment
from accounts.models import User
from notifications.models import SMSSettings, SMSLog, ProjectExpertNotification
from utils.ippanel import IPPanelClient

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Sends SMS notifications to province managers for inactive projects'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting SMS notification check...'))
        
        # Get SMS settings
        sms_settings = SMSSettings.get_settings()
        
        if not sms_settings.enabled:
            self.stdout.write(self.style.WARNING('SMS notifications are disabled in settings'))
            return
        
        # Get current date and calculate the threshold date
        now = timezone.now()
        threshold_date = now - datetime.timedelta(days=sms_settings.inactivity_days)
        
        # Find inactive projects (not updated in the specified period)
        inactive_projects = Project.objects.filter(
            updated_at__lt=threshold_date,
            is_approved=True  # Only consider approved projects
        )
        
        self.stdout.write(f'Found {inactive_projects.count()} inactive projects')
        
        # Group projects by province
        province_projects = {}
        for project in inactive_projects:
            if project.province not in province_projects:
                province_projects[project.province] = []
            province_projects[project.province].append(project)
        
        # Get province managers for each province with inactive projects
        for province, projects in province_projects.items():
            province_managers = User.objects.filter(
                role='PROVINCE_MANAGER',
                province=province,
                is_active=True
            )
            
            if not province_managers:
                self.stdout.write(self.style.WARNING(f'No province manager found for {province}'))
                continue
            
            # Send SMS to each province manager
            for manager in province_managers:
                if not manager.phone_number:
                    self.stdout.write(self.style.WARNING(f'No phone number for user {manager.username}'))
                    continue
                
                # Send SMS for each project
                for project in projects:
                    self._send_project_sms(manager, project, sms_settings)
                    
                    # Create notification record
                    ProjectExpertNotification.objects.create(
                        project=project,
                        expert=manager,
                        notification_type='project_update',
                        notified_via_sms=True
                    )
        
        # Update last run timestamp
        sms_settings.last_run = now
        sms_settings.save()
        
        self.stdout.write(self.style.SUCCESS('SMS notification check completed'))
    
    def _send_project_sms(self, user, project, sms_settings):
        """Send SMS notification for a specific project"""
        try:
            # Format the message
            message = sms_settings.message_template.format(
                project_name=project.name
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
            
            # Initialize SMS client
            sms_client = IPPanelClient(api_key=sms_settings.api_key)
            
            # Send SMS
            result = sms_client.send_sms(
                recipient_numbers=user.phone_number,
                message_text=message,
                sender_number=sms_settings.sender_number
            )
            
            with transaction.atomic():
                if result.get('meta', {}).get('status') == True:
                    # Update log with success
                    message_id = result.get('data', {}).get('message_id')
                    sms_log.status = 'sent'
                    sms_log.message_id = message_id
                    self.stdout.write(self.style.SUCCESS(
                        f'SMS sent to {user.username} ({user.phone_number}) for project {project.name}'
                    ))
                else:
                    # Update log with error
                    error_message = result.get('meta', {}).get('message', 'Unknown error')
                    sms_log.status = 'failed'
                    sms_log.error_message = error_message
                    self.stdout.write(self.style.ERROR(
                        f'Failed to send SMS to {user.username}: {error_message}'
                    ))
                
                sms_log.save()
                
        except Exception as e:
            logger.error(f"Error sending SMS for project {project.name}: {str(e)}")
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}')) 