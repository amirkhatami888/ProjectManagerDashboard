from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from creator_project.models import Project
from activity_monitor.utils import log_project_change
from activity_monitor.models import ProjectChangeLog
import uuid

User = get_user_model()

class Command(BaseCommand):
    help = 'Test project change tracking functionality'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Testing project change tracking...'))
        
        # Generate unique email for testing
        unique_id = str(uuid.uuid4())[:8]
        test_email = f'test_{unique_id}@example.com'
        
        # Get or create a test user
        user, created = User.objects.get_or_create(
            username=f'test_user_{unique_id}',
            defaults={
                'email': test_email,
                'first_name': 'Test',
                'last_name': 'User'
            }
        )
        
        if created:
            self.stdout.write(f'Created test user: {user.username}')
        else:
            self.stdout.write(f'Using existing test user: {user.username}')
        
        # Get or create a test project
        project, created = Project.objects.get_or_create(
            name=f'پروژه تست تغییرات {unique_id}',
            defaults={
                'project_type': 'احداث',
                'province': 'تهران',
                'city': 'تهران',
                'physical_progress': 0,
                'created_by': user
            }
        )
        
        if created:
            self.stdout.write(f'Created test project: {project.name}')
        else:
            self.stdout.write(f'Using existing test project: {project.name}')
        
        # Test logging various types of changes
        test_changes = [
            {
                'change_type': 'CREATE',
                'field_name': '',
                'old_value': '',
                'new_value': project.name,
                'description': f'پروژه جدید ایجاد شد: {project.name}',
                'related_object_type': 'Project'
            },
            {
                'change_type': 'UPDATE',
                'field_name': 'physical_progress',
                'old_value': '0',
                'new_value': '25.5',
                'description': f'فیلد پیشرفت فیزیکی در پروژه {project.name} تغییر یافت',
                'related_object_type': 'Project'
            },
            {
                'change_type': 'UPDATE',
                'field_name': 'project_type',
                'old_value': 'احداث',
                'new_value': 'تکمیل',
                'description': f'فیلد نوع پروژه در پروژه {project.name} تغییر یافت',
                'related_object_type': 'Project'
            },
            {
                'change_type': 'UPDATE',
                'field_name': 'contract_amount',
                'old_value': '0',
                'new_value': '1000000000',
                'description': f'فیلد مبلغ قرارداد در زیرپروژه تغییر یافت',
                'related_object_type': 'SubProject'
            }
        ]
        
        for change in test_changes:
            log_project_change(
                project_id=project.project_id,
                project_name=project.name,
                change_type=change['change_type'],
                change_description=change['description'],
                user=user,
                field_name=change['field_name'],
                old_value=change['old_value'],
                new_value=change['new_value'],
                related_object_type=change['related_object_type'],
                related_object_id=project.project_id
            )
        
        # Display the logged changes
        changes = ProjectChangeLog.objects.filter(project_id=project.project_id).order_by('-timestamp')
        
        self.stdout.write(self.style.SUCCESS(f'\nLogged {changes.count()} changes:'))
        for change in changes:
            self.stdout.write(f'\n- {change.timestamp}: {change.change_description}')
            self.stdout.write(f'  Field: {change.field_name} (Original: {change.original_field_name})')
            if change.old_value or change.new_value:
                self.stdout.write(f'  Values: {change.old_value} → {change.new_value}')
            self.stdout.write(f'  User: {change.user.username if change.user else "System"}')
        
        self.stdout.write(self.style.SUCCESS('\nTest completed successfully!'))
        self.stdout.write(f'You can view these changes at: http://127.0.0.1:8000/activity-monitor/project-changes/')
