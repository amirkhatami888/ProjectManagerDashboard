from django.core.management.base import BaseCommand
from django.utils import timezone
from creator_project.models import FundingRequest
from notifications_sms.models import SMSTemplate

class Command(BaseCommand):
    help = 'Test funding request SMS notification'

    def add_arguments(self, parser):
        parser.add_argument(
            '--funding-request-id',
            type=int,
            help='ID of the funding request to test SMS for',
        )

    def handle(self, *args, **options):
        funding_request_id = options.get('funding_request_id')
        
        if funding_request_id:
            try:
                funding_request = FundingRequest.objects.get(id=funding_request_id)
                self.stdout.write(f"Testing SMS for funding request: {funding_request}")
                
                # Get template
                template = SMSTemplate.objects.filter(
                    type=SMSTemplate.FUNDING_REQUEST_APPROVED,
                    is_default=True
                ).first()
                
                if not template:
                    self.stdout.write(
                        self.style.ERROR('No default funding approval template found')
                    )
                    return
                
                self.stdout.write(f"Using template: {template.name}")
                self.stdout.write(f"Template content:\n{template.content}")
                
                # Test the SMS sending without actually sending
                if funding_request.created_by.phone_number:
                    self.stdout.write(f"Would send SMS to: {funding_request.created_by.phone_number}")
                    self.stdout.write(f"Recipient: {funding_request.created_by.get_full_name()}")
                else:
                    self.stdout.write(
                        self.style.WARNING('User has no phone number set')
                    )
                
            except FundingRequest.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Funding request with ID {funding_request_id} not found')
                )
        else:
            # List available funding requests
            self.stdout.write("Available funding requests:")
            funding_requests = FundingRequest.objects.all()[:10]
            
            for fr in funding_requests:
                self.stdout.write(
                    f"ID: {fr.id} | Project: {fr.project.name} | Status: {fr.status} | Creator: {fr.created_by.get_full_name()}"
                )
            
            # Show template info
            template = SMSTemplate.objects.filter(
                type=SMSTemplate.FUNDING_REQUEST_APPROVED
            ).first()
            
            if template:
                self.stdout.write(f"\nFunding approval template found: {template.name}")
                self.stdout.write(f"Content preview:\n{template.content[:200]}...")
            else:
                self.stdout.write(
                    self.style.WARNING('\nNo funding approval template found')
                ) 