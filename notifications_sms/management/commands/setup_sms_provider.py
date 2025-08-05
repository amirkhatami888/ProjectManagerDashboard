from django.core.management.base import BaseCommand
from notifications_sms.models import SMSProvider, SMSSettings


class Command(BaseCommand):
    help = 'Setup a default SMS provider for testing'

    def handle(self, *args, **options):
        # Create or get a default SMS provider
        provider, created = SMSProvider.objects.get_or_create(
            name='IPPanel - FarazSMS',
            defaults={
                'base_url': 'http://edge.ippanel.com/v1/api/acl/message/sms/send',
                'api_key': 'OWVlNWZlOWEtOTVhOC00YmM3LTliYWMtNTk0Y2Y1ZTg4MGI3NjU1NWNjMTgzMThmNWVkYmY3OWFjZWJjNzczNzI3N2I=',
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Created new SMS provider: {provider.name}')
            )
        else:
            # Update to active
            provider.is_active = True
            provider.save()
            self.stdout.write(
                self.style.SUCCESS(f'Updated existing SMS provider: {provider.name}')
            )
        
        # Set this provider in settings
        settings = SMSSettings.get_settings()
        settings.provider = provider
        settings.save()
        
        self.stdout.write(
            self.style.SUCCESS(f'SMS provider "{provider.name}" has been set as active')
        )
        self.stdout.write(
            self.style.WARNING('Note: Please update the API key in the admin panel with your actual credentials')
        ) 