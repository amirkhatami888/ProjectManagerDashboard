from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from activity_monitor.models import ActivityLog, SystemEvent, ActivityDashboard
from activity_monitor.utils import log_activity, log_system_event, update_daily_dashboard
from datetime import datetime, timedelta
import random

User = get_user_model()


class Command(BaseCommand):
    help = 'Initialize activity monitor with sample data and test functionality'

    def add_arguments(self, parser):
        parser.add_argument(
            '--sample-data',
            action='store_true',
            help='Create sample activity data',
        )
        parser.add_argument(
            '--test-logging',
            action='store_true',
            help='Test logging functionality',
        )
        parser.add_argument(
            '--update-dashboard',
            action='store_true',
            help='Update daily dashboard statistics',
        )

    def handle(self, *args, **options):
        if options['sample_data']:
            self.create_sample_data()
        
        if options['test_logging']:
            self.test_logging()
        
        if options['update_dashboard']:
            self.update_dashboard()
        
        if not any(options.values()):
            self.stdout.write(
                self.style.SUCCESS('Activity Monitor initialized successfully!')
            )
            self.stdout.write('Use --sample-data to create sample data')
            self.stdout.write('Use --test-logging to test logging functionality')
            self.stdout.write('Use --update-dashboard to update dashboard statistics')

    def create_sample_data(self):
        """Create sample activity data"""
        self.stdout.write('Creating sample activity data...')
        
        # Get or create a test user
        user, created = User.objects.get_or_create(
            username='test_monitor',
            defaults={
                'email': 'test@example.com',
                'role': 'ADMIN',
                'is_staff': True,
            }
        )
        
        if created:
            user.set_password('testpass123')
            user.save()
            self.stdout.write(f'Created test user: {user.username}')
        
        # Create sample activity logs
        activities = [
            ('LOGIN', 'User logged in successfully'),
            ('VIEW', 'Viewed project dashboard'),
            ('CREATE', 'Created new project'),
            ('UPDATE', 'Updated project details'),
            ('DOWNLOAD', 'Downloaded project report'),
            ('APPROVE', 'Approved funding request'),
            ('REJECT', 'Rejected project proposal'),
            ('COMMENT', 'Added comment to project'),
            ('UPLOAD', 'Uploaded project document'),
        ]
        
        for i in range(20):
            activity_type, description = random.choice(activities)
            timestamp = timezone.now() - timedelta(
                hours=random.randint(1, 168),  # Last 7 days
                minutes=random.randint(0, 59)
            )
            
            ActivityLog.objects.create(
                user=user,
                activity_type=activity_type,
                description=f'{description} #{i+1}',
                timestamp=timestamp,
                ip_address=f'192.168.1.{random.randint(1, 255)}',
                severity=random.choice(['LOW', 'MEDIUM', 'HIGH']),
                details={
                    'sample_data': True,
                    'iteration': i+1,
                }
            )
        
        # Create sample system events
        events = [
            ('INFO', 'System maintenance completed', 'LOW'),
            ('WARNING', 'High memory usage detected', 'MEDIUM'),
            ('ERROR', 'Database connection timeout', 'HIGH'),
            ('SECURITY', 'Failed login attempt', 'MEDIUM'),
            ('PERFORMANCE', 'Slow query detected', 'MEDIUM'),
        ]
        
        for i in range(10):
            event_type, title, severity = random.choice(events)
            timestamp = timezone.now() - timedelta(
                hours=random.randint(1, 72),  # Last 3 days
                minutes=random.randint(0, 59)
            )
            
            SystemEvent.objects.create(
                event_type=event_type,
                title=f'{title} #{i+1}',
                description=f'Sample system event for testing purposes',
                severity=severity,
                component=random.choice(['Database', 'Web Server', 'Application', 'Security']),
                timestamp=timestamp,
                details={
                    'sample_data': True,
                    'iteration': i+1,
                }
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'Created {ActivityLog.objects.count()} activity logs and {SystemEvent.objects.count()} system events')
        )

    def test_logging(self):
        """Test logging functionality"""
        self.stdout.write('Testing logging functionality...')
        
        # Test activity logging
        log_activity(
            activity_type='TEST',
            description='Test activity log from management command',
            details={'test': True, 'timestamp': timezone.now().isoformat()}
        )
        
        # Test system event logging
        log_system_event(
            event_type='INFO',
            title='Test System Event',
            description='Test system event from management command',
            severity='LOW',
            component='Management',
            details={'test': True, 'timestamp': timezone.now().isoformat()}
        )
        
        self.stdout.write(
            self.style.SUCCESS('Logging functionality tested successfully!')
        )

    def update_dashboard(self):
        """Update daily dashboard statistics"""
        self.stdout.write('Updating daily dashboard statistics...')
        
        # Update today's dashboard
        dashboard = update_daily_dashboard()
        
        if dashboard:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Dashboard updated for {dashboard.date}: '
                    f'{dashboard.total_activities} activities, '
                    f'{dashboard.total_logins} logins, '
                    f'{dashboard.total_project_changes} project changes, '
                    f'{dashboard.total_system_events} system events'
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING('Failed to update dashboard')
            )
