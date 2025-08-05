from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q
from django.conf import settings
from django.db import transaction
import logging
import datetime

from creator_project.models import Project
from accounts.models import User, ExpertProvince
from notifications.models import ExpertReminderSMSSettings, SMSSettings, SMSLog, ProjectExpertNotification
from utils.ippanel import IPPanelClient

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Sends SMS reminders to experts who have not examined projects for the specified period'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting expert reminder SMS check...'))
        
        # Get SMS settings
        sms_settings = ExpertReminderSMSSettings.get_settings()
        
        if not sms_settings.enabled:
            self.stdout.write(self.style.WARNING('Expert reminder SMS notifications are disabled in settings'))
            return
        
        # Get current date and calculate the threshold date
        now = timezone.now()
        threshold_date = now - datetime.timedelta(days=sms_settings.reminder_days)
        
        # Find projects submitted but not examined by experts
        pending_projects = Project.objects.filter(
            is_submitted=True,
            is_expert_approved=False,
            created_at__lt=threshold_date
        )
        
        self.stdout.write(f'Found {pending_projects.count()} pending projects waiting for expert review')
        
        # Group projects by province
        province_projects = {}
        for project in pending_projects:
            if project.province not in province_projects:
                province_projects[project.province] = []
            province_projects[project.province].append(project)
        
        # Get experts for each province with pending projects
        for province, projects in province_projects.items():
            # Find experts assigned to this province
            expert_provinces = ExpertProvince.objects.filter(province=province)
            experts = User.objects.filter(id__in=expert_provinces.values_list('expert', flat=True), is_active=True)
            
            if not experts:
                self.stdout.write(self.style.WARNING(f'No experts found for province {province}'))
                continue
            
            # Send SMS to each expert
            for expert in experts:
                if not expert.phone_number:
                    self.stdout.write(self.style.WARNING(f'No phone number for expert {expert.username}'))
                    continue
                
                # Send reminder for each project
                for project in projects:
                    # Check if already notified recently
                    existing_notification = ProjectExpertNotification.objects.filter(
                        project=project,
                        expert=expert,
                        notification_type='expert_reminder',
                        created_at__gt=threshold_date
                    ).exists()
                    
                    if existing_notification:
                        self.stdout.write(self.style.WARNING(
                            f'Expert {expert.username} already reminded about project {project.name}'
                        ))
                        continue
                    
                    # Send the reminder SMS
                    self._send_reminder_sms(expert, project, sms_settings)
                    
                    # Create notification record
                    ProjectExpertNotification.objects.create(
                        project=project,
                        expert=expert,
                        notification_type='expert_reminder',
                        notified_via_sms=True
                    )
        
        # Update last run timestamp
        sms_settings.last_run = now
        sms_settings.save()
        
        self.stdout.write(self.style.SUCCESS('Expert reminder SMS check completed'))
    
    def _send_reminder_sms(self, expert, project, sms_settings):
        """Send SMS reminder to an expert for a specific project"""
        try:
            # Format the message
            message = sms_settings.message_template.format(
                project_name=project.name
            )
            
            # Create SMS log entry
            sms_log = SMSLog.objects.create(
                recipient=expert,
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
                recipient_numbers=expert.phone_number,
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
                        f'Reminder SMS sent to expert {expert.username} ({expert.phone_number}) for project {project.name}'
                    ))
                else:
                    # Update log with error
                    error_message = result.get('meta', {}).get('message', 'Unknown error')
                    sms_log.status = 'failed'
                    sms_log.error_message = error_message
                    self.stdout.write(self.style.ERROR(
                        f'Failed to send reminder SMS to expert {expert.username}: {error_message}'
                    ))
                
                sms_log.save()
                
        except Exception as e:
            logger.error(f"Error sending reminder SMS for project {project.name}: {str(e)}")
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}')) 