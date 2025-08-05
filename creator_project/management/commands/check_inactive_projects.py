import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q
from django.contrib.auth import get_user_model
from creator_project.models import Project, SMSConfiguration
from utils.ippanel import IPPanelClient

User = get_user_model()

class Command(BaseCommand):
    help = 'Check for inactive projects and send SMS notifications'

    def handle(self, *args, **options):
        # Get active SMS configurations
        configurations = SMSConfiguration.objects.filter(enabled=True)
        
        if not configurations.exists():
            self.stdout.write(self.style.WARNING('No active SMS configurations found'))
            return
        
        for config in configurations:
            # Calculate the threshold date
            threshold_date = timezone.now() - datetime.timedelta(days=config.inactive_days_threshold)
            
            # Build the query for inactive projects
            query = Q(last_updated__lt=threshold_date)
            
            # Add province filter if specified
            if config.province:
                query &= Q(province=config.province)
            
            # Find inactive projects
            inactive_projects = Project.objects.filter(query)
            
            if not inactive_projects.exists():
                self.stdout.write(f'No inactive projects found for config {config.id}')
                continue
            
            # Group projects by province
            province_projects = {}
            for project in inactive_projects:
                if project.province not in province_projects:
                    province_projects[project.province] = []
                province_projects[project.province].append(project)
            
            # Send notifications for each province
            client = IPPanelClient()
            
            for province, projects in province_projects.items():
                # Get users from this province
                province_users = User.objects.filter(profile__province=province)
                
                if not province_users.exists():
                    self.stdout.write(f'No users found for province {province}')
                    continue
                
                # Collect mobile numbers
                mobile_numbers = []
                for user in province_users:
                    if user.profile.mobile and user.profile.receive_sms:
                        mobile_numbers.append(user.profile.mobile)
                
                if not mobile_numbers:
                    self.stdout.write(f'No mobile numbers found for province {province}')
                    continue
                
                # Send SMS for each inactive project
                for project in projects:
                    message = config.message_template.format(project_name=project.name)
                    result = client.send_sms(mobile_numbers, message)
                    self.stdout.write(f'Sent {len(mobile_numbers)} SMS for project {project.name} in {province}')
            
            # Update last run time
            config.last_run = timezone.now()
            config.save() 