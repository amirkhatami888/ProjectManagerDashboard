from django.core.management.base import BaseCommand
from notifications_sms.utils import IPPanelSMSSender
from notifications_sms.models import SMSProvider

class Command(BaseCommand):
    help = 'Test IPPanel SMS integration'

    def add_arguments(self, parser):
        parser.add_argument('--phone', type=str, help='Phone number to send test SMS to')
        parser.add_argument('--api-key', type=str, help='IPPanel API key to test')
        parser.add_argument('--originator', type=str, default='+985000404223', help='Sender number')

    def handle(self, *args, **options):
        phone = options.get('phone')
        api_key = options.get('api_key')
        originator = options.get('originator')

        if not phone:
            self.stdout.write(self.style.ERROR('Please provide --phone argument'))
            return

        if api_key:
            # Create or update test provider
            provider, created = SMSProvider.objects.get_or_create(
                name='Test IPPanel',
                defaults={
                    'api_key': api_key,
                    'sender_number': originator,
                    'provider_type': 'IPPANEL',
                    'is_active': True
                }
            )
            if not created:
                provider.api_key = api_key
                provider.sender_number = originator
                provider.is_active = True
                provider.save()
            
            # Deactivate other providers
            SMSProvider.objects.exclude(pk=provider.pk).update(is_active=False)
            
            self.stdout.write(self.style.SUCCESS(f'Updated provider: {provider.name}'))

        # Test credit check
        self.stdout.write('Checking credit...')
        credit_result = IPPanelSMSSender.get_credit()
        if credit_result['status'] == 'OK':
            self.stdout.write(self.style.SUCCESS(f'Credit: {credit_result["credit"]}'))
        else:
            self.stdout.write(self.style.ERROR(f'Credit check failed: {credit_result["message"]}'))
            return

        # Test SMS sending
        self.stdout.write(f'Sending test SMS to {phone}...')
        test_message = 'این یک پیام تست از سیستم مدیریت پروژه است. IPPanel SDK Test'
        
        result = IPPanelSMSSender.send_sms(
            phone,
            test_message,
            sender_user=None
        )
        
        if result['status'] == 'OK':
            self.stdout.write(self.style.SUCCESS(f'SMS sent successfully! Message ID: {result.get("message_id", "N/A")}'))
        else:
            self.stdout.write(self.style.ERROR(f'SMS sending failed: {result["message"]}')) 