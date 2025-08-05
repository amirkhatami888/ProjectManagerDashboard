from django.core.management.base import BaseCommand
from django.conf import settings
from webhooks.models import WebhookConfiguration
from webhooks.utils import process_webhook_event


class Command(BaseCommand):
    help = 'Test webhook functionality with sample data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--repository',
            type=str,
            help='Repository URL to test with',
        )
        parser.add_argument(
            '--event-type',
            type=str,
            default='push',
            choices=['push', 'pull_request', 'release', 'issues'],
            help='Event type to simulate',
        )

    def handle(self, *args, **options):
        repository = options['repository']
        event_type = options['event_type']

        if not repository:
            # Try to get the first configured repository
            config = WebhookConfiguration.objects.filter(is_active=True).first()
            if config:
                repository = config.repository_url
            else:
                self.stdout.write(
                    self.style.ERROR('No webhook configuration found. Please create one first.')
                )
                return

        # Sample payload based on event type
        if event_type == 'push':
            payload = {
                'ref': 'refs/heads/main',
                'repository': {
                    'full_name': repository.split('/')[-2] + '/' + repository.split('/')[-1]
                },
                'head_commit': {
                    'id': 'test-commit-sha-123456789',
                    'message': 'Test commit message'
                }
            }
        elif event_type == 'pull_request':
            payload = {
                'pull_request': {
                    'number': 1,
                    'title': 'Test Pull Request',
                    'head': {
                        'ref': 'feature-branch',
                        'sha': 'test-pr-sha-123456789'
                    }
                },
                'repository': {
                    'full_name': repository.split('/')[-2] + '/' + repository.split('/')[-1]
                }
            }
        elif event_type == 'release':
            payload = {
                'release': {
                    'name': 'v1.0.0',
                    'tag_name': 'v1.0.0'
                },
                'repository': {
                    'full_name': repository.split('/')[-2] + '/' + repository.split('/')[-1]
                }
            }
        else:  # issues
            payload = {
                'issue': {
                    'number': 1,
                    'title': 'Test Issue'
                },
                'repository': {
                    'full_name': repository.split('/')[-2] + '/' + repository.split('/')[-1]
                }
            }

        # Parse event data
        from webhooks.utils import parse_github_event
        event_data = parse_github_event(payload)

        self.stdout.write(f'Testing webhook for repository: {repository}')
        self.stdout.write(f'Event type: {event_type}')
        self.stdout.write(f'Event data: {event_data}')

        # Process the webhook event
        success, message = process_webhook_event(event_data, payload)

        if success:
            self.stdout.write(
                self.style.SUCCESS(f'Webhook test successful: {message}')
            )
        else:
            self.stdout.write(
                self.style.ERROR(f'Webhook test failed: {message}')
            ) 