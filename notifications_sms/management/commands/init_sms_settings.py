from django.core.management.base import BaseCommand
from django.utils.translation import gettext_lazy as _

from notifications_sms.models import SMSTemplate, SMSSettings, SMSProvider


class Command(BaseCommand):
    help = 'Initialize SMS settings with default templates and provider'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Initializing SMS settings...'))
        
        # Create or update the IPPanel provider
        provider, created = SMSProvider.objects.update_or_create(
            name="IPPanel - FarazSMS",
            defaults={
                'base_url': "http://edge.ippanel.com/v1/api/acl/message/sms/send",
                'api_key': "OWVlNWZlOWEtOTVhOC00YmM3LTliYWMtNTk0Y2Y1ZTg4MGI3NjU1NWNjMTgzMThmNWVkYmY3OWFjZWJjNzczNzI3N2I=",
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('Created IPPanel provider'))
        else:
            self.stdout.write(self.style.SUCCESS('Updated IPPanel provider'))
        
        # Update SMS settings to use this provider
        settings = SMSSettings.get_settings()
        settings.provider = provider
        settings.outdated_project_days = 30  # Default to 30 days
        settings.not_examined_days = 3  # Default to 3 days
        settings.save()
        
        self.stdout.write(self.style.SUCCESS('Updated SMS settings to use IPPanel provider'))
        
        # Create default templates
        self._create_default_templates()
        
        self.stdout.write(self.style.SUCCESS('SMS settings initialized successfully!'))
    
    def _create_default_templates(self):
        """Create default SMS templates if they don't exist"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Get the first admin user (using role field instead of is_admin property)
        admin_user = User.objects.filter(role='ADMIN').first()
        if not admin_user:
            self.stdout.write(self.style.WARNING('No admin user found for template creation'))
            return
        
        templates = [
            {
                'name': 'Default Project Outdated Notification',
                'type': 'PROJECT_OUTDATED',
                'content': 'با سلام وعرض ادب خدمت همکار گرامی لطفا به بروزسانی وضعیت پروژه {name of project} اقدام فرمایید',
                'is_default': True
            },
            {
                'name': 'Default Project Rejected Notification',
                'type': 'PROJECT_REJECTED',
                'content': 'با سلام وعرض ادب خدمت همکار گرامی به دلیل زیر پروژه نیازمند اصلاح است {reason of rejection}',
                'is_default': True
            },
            {
                'name': 'Default Project Not Examined Notification',
                'type': 'PROJECT_NOT_EXAMINED',
                'content': 'با سلام وعرض ادب خدمت همکار گرامی لطفا به وضعیت پروژه {name of project} اقدام فرمایید',
                'is_default': True
            }
        ]
        
        for template_data in templates:
            template, created = SMSTemplate.objects.update_or_create(
                name=template_data['name'],
                defaults={
                    'type': template_data['type'],
                    'content': template_data['content'],
                    'is_default': template_data['is_default'],
                    'created_by': admin_user
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created template: {template.name}'))
            else:
                self.stdout.write(self.style.SUCCESS(f'Updated template: {template.name}')) 