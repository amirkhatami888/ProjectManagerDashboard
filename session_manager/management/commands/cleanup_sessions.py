from django.core.management.base import BaseCommand
from django.contrib.sessions.models import Session
from django.utils import timezone
from session_manager.models import SessionLog

class Command(BaseCommand):
    help = 'Clean up expired sessions and session logs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Clean up expired sessions
        expired_sessions = Session.objects.filter(expire_date__lt=timezone.now())
        expired_count = expired_sessions.count()
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'Would delete {expired_count} expired sessions')
            )
        else:
            deleted_sessions = expired_sessions.delete()
            self.stdout.write(
                self.style.SUCCESS(f'Deleted {deleted_sessions[0]} expired sessions')
            )
        
        # Clean up old session logs
        old_logs = SessionLog.objects.filter(
            last_activity__lt=timezone.now() - timezone.timedelta(days=30)
        )
        old_logs_count = old_logs.count()
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'Would delete {old_logs_count} old session logs')
            )
        else:
            deleted_logs = old_logs.delete()
            self.stdout.write(
                self.style.SUCCESS(f'Deleted {deleted_logs[0]} old session logs')
            )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('Dry run completed. Use without --dry-run to actually delete.')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('Session cleanup completed successfully.')
            )
