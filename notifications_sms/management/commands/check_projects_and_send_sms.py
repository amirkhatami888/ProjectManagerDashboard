from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q

from notifications_sms.models import SMSTemplate, SMSSettings
from notifications_sms.utils import IPPanelSMSSender
from creator_project.models import Project
from creator_subproject.models import SubProject
from accounts.models import User


class Command(BaseCommand):
    help = 'Check projects status and send SMS notifications based on rules'

    def handle(self, *args, **options):
        self.settings = SMSSettings.get_settings()
        self.stdout.write(self.style.SUCCESS('Starting project check for SMS notifications...'))
        
        self.check_outdated_projects()
        self.check_not_examined_projects()
        
        self.stdout.write(self.style.SUCCESS('Project check complete!'))
    
    def check_outdated_projects(self):
        """Check for projects that haven't been updated for a long time"""
        if not self.settings.outdated_project_days:
            self.stdout.write(self.style.WARNING('No outdated_project_days set in SMS settings, skipping check'))
            return
            
        outdated_date = timezone.now() - timedelta(days=self.settings.outdated_project_days)
        outdated_projects = Project.objects.filter(
            updated_at__lt=outdated_date,
            status__in=['ONGOING', 'PLANNED']  # Only check active projects
        )
        
        self.stdout.write(f'Found {outdated_projects.count()} outdated projects')
        
        # Group projects by province to minimize messages
        projects_by_province = {}
        for project in outdated_projects:
            if project.province not in projects_by_province:
                projects_by_province[project.province] = []
            projects_by_province[project.province].append(project)
        
        # Get the template
        template = SMSTemplate.objects.filter(
            type='PROJECT_OUTDATED', 
            is_default=True
        ).first()
        
        if not template:
            self.stdout.write(self.style.ERROR('No default PROJECT_OUTDATED template found'))
            return
        
        # Send SMS for each province
        for province, projects in projects_by_province.items():
            # Get managers in this province
            managers = User.objects.filter(
                province=province,
                is_active=True,
                is_province_manager=True
            )
            
            for project in projects:
                for manager in managers:
                    if not manager.phone_number:
                        continue
                        
                    message = template.content.replace('{name of project}', project.name)
                    
                    # Send the SMS
                    IPPanelSMSSender.send_sms(
                        manager.phone_number,
                        message,
                        recipient_user=manager,
                        template=template
                    )
                    
                    self.stdout.write(f'Sent outdated project SMS for {project.name} to {manager.username}')
    
    def check_not_examined_projects(self):
        """Check for projects assigned to experts but not examined for a while"""
        if not self.settings.not_examined_days:
            self.stdout.write(self.style.WARNING('No not_examined_days set in SMS settings, skipping check'))
            return
            
        delay_date = timezone.now() - timedelta(days=self.settings.not_examined_days)
        
        # Find subprojects assigned to experts but not examined
        unexamined_subprojects = SubProject.objects.filter(
            assigned_expert__isnull=False,
            last_expert_check__lt=delay_date
        )
        
        self.stdout.write(f'Found {unexamined_subprojects.count()} unexamined subprojects')
        
        # Get the template
        template = SMSTemplate.objects.filter(
            type='PROJECT_NOT_EXAMINED', 
            is_default=True
        ).first()
        
        if not template:
            self.stdout.write(self.style.ERROR('No default PROJECT_NOT_EXAMINED template found'))
            return
        
        # Send SMS to each expert
        for subproject in unexamined_subprojects:
            expert = subproject.assigned_expert
            
            if not expert or not expert.phone_number:
                continue
                
            message = template.content.replace('{name of project}', subproject.name)
            
            # Send the SMS
            IPPanelSMSSender.send_sms(
                expert.phone_number,
                message,
                recipient_user=expert,
                template=template
            )
            
            self.stdout.write(f'Sent unexamined project SMS for {subproject.name} to {expert.username}') 