import logging
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from django.db.models import Q

from creator_project.models import Project
from creator_review.models import ProjectReview
from accounts.models import User
from notifications_sms.models import SMSSettings
from notifications_sms.utils import (
    IPPanelSMSSender, 
    format_project_outdated_message,
    format_project_not_examined_message
)

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Checks projects and sends SMS notifications for outdated projects and unexamined projects'
    
    def handle(self, *args, **options):
        self.stdout.write('Starting project checks for SMS notifications...')
        
        # Get settings
        sms_settings = SMSSettings.get_settings()
        
        # Check outdated projects (not updated for more than settings.outdated_project_days)
        self.check_outdated_projects(sms_settings.outdated_project_days)
        
        # Check unexamined projects (not examined by assigned expert for more than settings.not_examined_days)
        self.check_unexamined_projects(sms_settings.not_examined_days)
        
        self.stdout.write(self.style.SUCCESS('Project check completed.'))
        
    def check_outdated_projects(self, days):
        """Check for projects not updated in specified days"""
        self.stdout.write(f'Checking for projects not updated in {days} days...')
        
        # Calculate the date threshold
        outdated_threshold = timezone.now() - timedelta(days=days)
        
        # Get projects not updated since the threshold
        outdated_projects = Project.objects.filter(
            updated_at__lt=outdated_threshold,
            status__in=['PENDING', 'IN_PROGRESS']  # Only check active projects
        )
        
        self.stdout.write(f'Found {outdated_projects.count()} outdated projects')
        
        # Send notifications to province managers
        for project in outdated_projects:
            # Get province manager(s) for the project's province
            province_managers = User.objects.filter(
                Q(role='PROVINCE_MANAGER') & 
                Q(province=project.province)
            )
            
            if not province_managers.exists():
                self.stdout.write(f'No province manager found for project {project.id} in province {project.province}')
                continue
            
            # Format message
            message = format_project_outdated_message(project.name)
            
            # Send SMS to each province manager
            for manager in province_managers:
                if not manager.phone_number:
                    self.stdout.write(f'Province manager {manager.username} has no phone number')
                    continue
                
                self.stdout.write(f'Sending outdated project notification for {project.name} to {manager.username}')
                
                # Send SMS
                response = IPPanelSMSSender.send_sms(
                    manager.phone_number,
                    message,
                    recipient_user=manager
                )
                
                if response.get('status') != 'OK':
                    self.stdout.write(self.style.ERROR(
                        f'Failed to send SMS to {manager.username}: {response.get("message", "Unknown error")}'
                    ))
    
    def check_unexamined_projects(self, days):
        """Check for projects not examined by assigned expert in specified days"""
        self.stdout.write(f'Checking for projects not examined in {days} days...')
        
        # Calculate the date threshold
        unexamined_threshold = timezone.now() - timedelta(days=days)
        
        # Get projects that are pending expert review
        pending_projects = Project.objects.filter(
            status='UNDER_REVIEW',
            updated_at__lt=unexamined_threshold
        )
        
        self.stdout.write(f'Found {pending_projects.count()} unexamined projects')
        
        for project in pending_projects:
            # Find assigned expert(s) who have not yet reviewed
            pending_reviews = ProjectReview.objects.filter(
                project=project,
                status='PENDING'
            )
            
            if not pending_reviews.exists():
                self.stdout.write(f'No pending reviews found for project {project.id}')
                continue
            
            # Send notification to each expert
            for review in pending_reviews:
                expert = review.expert
                
                if not expert or not expert.phone_number:
                    self.stdout.write(f'Expert not found or has no phone number for review {review.id}')
                    continue
                
                # Format message
                message = format_project_not_examined_message(project.name)
                
                self.stdout.write(f'Sending unexamined project reminder for {project.name} to {expert.username}')
                
                # Send SMS
                response = IPPanelSMSSender.send_sms(
                    expert.phone_number,
                    message,
                    recipient_user=expert
                )
                
                if response.get('status') != 'OK':
                    self.stdout.write(self.style.ERROR(
                        f'Failed to send SMS to {expert.username}: {response.get("message", "Unknown error")}'
                    )) 