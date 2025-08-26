from django.core.management.base import BaseCommand
from django.utils import timezone
from activity_monitor.utils import cleanup_expired_sessions
from activity_monitor.models import UserSession
from datetime import timedelta


class Command(BaseCommand):
    help = 'Clean up expired user sessions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be cleaned up without actually doing it',
        )
        parser.add_argument(
            '--timeout',
            type=int,
            default=15,
            help='Session timeout in minutes (default: 15)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        timeout_minutes = options['timeout']
        
        self.stdout.write(
            self.style.SUCCESS(f'Starting session cleanup (timeout: {timeout_minutes} minutes)')
        )
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        # Get timeout threshold
        timeout_threshold = timezone.now() - timedelta(minutes=timeout_minutes)
        
        # Find expired sessions
        expired_sessions = UserSession.objects.filter(
            is_active=True,
            last_activity__lt=timeout_threshold
        ).select_related('user')
        
        expired_count = expired_sessions.count()
        
        if expired_count == 0:
            self.stdout.write(
                self.style.SUCCESS('No expired sessions found')
            )
            return
        
        self.stdout.write(
            self.style.WARNING(f'Found {expired_count} expired sessions')
        )
        
        # Show details of expired sessions
        for session in expired_sessions[:10]:  # Show first 10
            self.stdout.write(
                f'  - {session.user.username}: {session.last_activity} '
                f'(inactive for {timezone.now() - session.last_activity})'
            )
        
        if expired_count > 10:
            self.stdout.write(f'  ... and {expired_count - 10} more sessions')
        
        if not dry_run:
            # Actually clean up the sessions
            cleaned_count = cleanup_expired_sessions()
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully cleaned up {cleaned_count} expired sessions')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'Would clean up {expired_count} expired sessions')
            )
        
        # Show current session statistics
        total_sessions = UserSession.objects.count()
        active_sessions = UserSession.objects.filter(is_active=True).count()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Session statistics: {active_sessions} active / {total_sessions} total'
            )
        )
