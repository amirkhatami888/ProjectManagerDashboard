from django.core.management.base import BaseCommand
from django.utils.translation import gettext_lazy as _

from notifications_sms.utils import IPPanelSMSSender
from creator_project.models import Project
from creator_subproject.models import SubProject


class Command(BaseCommand):
    help = 'Send SMS notifications for rejected projects'
    
    def add_arguments(self, parser):
        parser.add_argument('project_id', type=int, help='ID of the project or subproject')
        parser.add_argument('--type', type=str, choices=['project', 'subproject'], default='project',
                            help='Type of the project (project or subproject)')
        parser.add_argument('--reason', type=str, required=True, help='Reason for rejection')
    
    def handle(self, *args, **options):
        project_id = options['project_id']
        project_type = options['type']
        reason = options['reason']
        
        if project_type == 'project':
            self._handle_project_rejection(project_id, reason)
        else:
            self._handle_subproject_rejection(project_id, reason)
    
    def _handle_project_rejection(self, project_id, reason):
        """Handle rejection of a main project"""
        try:
            project = Project.objects.get(id=project_id)
            
            # Get the project owner/manager
            recipient = project.created_by
            
            if not recipient or not recipient.phone_number:
                self.stdout.write(self.style.ERROR(f'Project #{project_id} has no owner with a phone number'))
                return
            
            # Send rejection SMS
            result = IPPanelSMSSender.send_project_rejected_sms(
                recipient, 
                project.name, 
                reason
            )
            
            if result.get('status') == 'OK':
                self.stdout.write(self.style.SUCCESS(
                    f'Successfully sent rejection SMS for project {project.name} to {recipient.username}'
                ))
            else:
                self.stdout.write(self.style.ERROR(
                    f'Failed to send rejection SMS: {result.get("message")}'
                ))
                
        except Project.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Project with ID {project_id} does not exist'))
    
    def _handle_subproject_rejection(self, subproject_id, reason):
        """Handle rejection of a subproject"""
        try:
            subproject = SubProject.objects.get(id=subproject_id)
            
            # Get the subproject owner/manager
            recipient = subproject.created_by
            
            if not recipient or not recipient.phone_number:
                self.stdout.write(self.style.ERROR(f'Subproject #{subproject_id} has no owner with a phone number'))
                return
            
            # Send rejection SMS
            result = IPPanelSMSSender.send_project_rejected_sms(
                recipient, 
                subproject.name, 
                reason
            )
            
            if result.get('status') == 'OK':
                self.stdout.write(self.style.SUCCESS(
                    f'Successfully sent rejection SMS for subproject {subproject.name} to {recipient.username}'
                ))
            else:
                self.stdout.write(self.style.ERROR(
                    f'Failed to send rejection SMS: {result.get("message")}'
                ))
                
        except SubProject.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Subproject with ID {subproject_id} does not exist')) 