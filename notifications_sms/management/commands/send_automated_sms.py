from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta
import logging

from notifications_sms.models import SMSSettings, SMSLog
from notifications_sms.utils import IPPanelSMSSender, get_default_template
from creator_project.models import Project
from creator_subproject.models import SubProject
from accounts.models import User

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Send automated SMS notifications based on project status and settings'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force sending even if interval has not passed',
        )
        parser.add_argument(
            '--type',
            choices=['outdated', 'not_examined', 'all'],
            default='all',
            help='Type of notifications to send',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting automated SMS sending...'))
        
        settings = SMSSettings.get_settings()
        if not settings or not settings.provider:
            self.stdout.write(self.style.ERROR('No SMS provider configured'))
            return
        
        force = options['force']
        notification_type = options['type']
        
        # Check if enough time has passed since last check
        if not force:
            last_log = SMSLog.objects.filter(
                message__contains='خودکار'  # Automated messages contain this word
            ).order_by('-sent_at').first()
            
            if last_log:
                time_since_last = timezone.now() - last_log.sent_at
                if time_since_last.total_seconds() < settings.check_interval_hours * 3600:
                    remaining_hours = settings.check_interval_hours - (time_since_last.total_seconds() / 3600)
                    self.stdout.write(
                        self.style.WARNING(
                            f'Not enough time passed since last check. '
                            f'Wait {remaining_hours:.1f} more hours or use --force'
                        )
                    )
                    return

        sent_count = 0
        
        # Send outdated project notifications
        if notification_type in ['outdated', 'all'] and settings.auto_send_outdated:
            sent_count += self.send_outdated_notifications(settings)
        
        # Send not examined project notifications
        if notification_type in ['not_examined', 'all'] and settings.auto_send_not_examined:
            sent_count += self.send_not_examined_notifications(settings)
        
        self.stdout.write(
            self.style.SUCCESS(f'Automated SMS sending completed. Sent {sent_count} messages.')
        )

    def send_outdated_notifications(self, settings):
        """Send notifications for outdated projects"""
        self.stdout.write('Checking for outdated projects...')
        
        cutoff_date = timezone.now() - timedelta(days=settings.outdated_project_days)
        
        # Find projects that haven't been updated in the specified time
        # Only consider submitted projects (not drafts)
        outdated_projects = Project.objects.filter(
            Q(updated_at__lt=cutoff_date) | Q(created_at__lt=cutoff_date, updated_at__isnull=True),
            is_submitted=True  # Only check submitted projects
        ).select_related('created_by')
        
        sent_count = 0
        template = get_default_template('PROJECT_OUTDATED')
        
        for project in outdated_projects:
            if not project.created_by.phone_number:
                continue
                
            # Check if we already sent a notification for this project recently
            recent_log = SMSLog.objects.filter(
                recipient_user=project.created_by,
                message__contains=project.name[:20],  # Check if message contains project name
                sent_at__gte=timezone.now() - timedelta(days=1)  # Within last day
            ).exists()
            
            if recent_log:
                continue
            
            if template:
                # Replace placeholders in template
                message = template.content
                if '{project_name}' in message:
                    message = message.replace('{project_name}', project.name)
                elif '{name of project}' in message:
                    message = message.replace('{name of project}', project.name)
                if '{user_name}' in message:
                    message = message.replace('{user_name}', project.created_by.get_full_name() or project.created_by.username)
                if '{days}' in message:
                    message = message.replace('{days}', str(settings.outdated_project_days))
            else:
                message = f"سلام {project.created_by.get_full_name()}\n" \
                         f"پروژه '{project.name}' شما {settings.outdated_project_days} روز است که بروزرسانی نشده. " \
                         f"لطفاً وضعیت پروژه را بروزرسانی کنید.\n" \
                         f"(ارسال خودکار سیستم)"
            
            result = FarazSMSSender.send_sms(
                recipient_number=project.created_by.phone_number,
                message=message,
                sender_user=None,  # System send
                recipient_user=project.created_by,
                template=template
            )
            
            if result['status'] == 'OK':
                sent_count += 1
                self.stdout.write(
                    f"✓ Sent outdated notification to {project.created_by.username} for project '{project.name}'"
                )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f"✗ Failed to send to {project.created_by.username}: {result['message']}"
                    )
                )
        
        self.stdout.write(f"Sent {sent_count} outdated project notifications")
        return sent_count

    def send_not_examined_notifications(self, settings):
        """Send notifications to experts for unexamined projects"""
        self.stdout.write('Checking for unexamined projects...')
        
        cutoff_date = timezone.now() - timedelta(days=settings.not_examined_days)
        
        # Find projects submitted for review but not examined
        unexamined_projects = Project.objects.filter(
            is_submitted=True,
            is_expert_approved=False,
            created_at__lt=cutoff_date
        ).select_related('created_by')
        
        # Group by province to send to relevant experts
        provinces_with_projects = {}
        for project in unexamined_projects:
            province = project.province
            if province not in provinces_with_projects:
                provinces_with_projects[province] = []
            provinces_with_projects[province].append(project)
        
        sent_count = 0
        template = get_default_template('PROJECT_NOT_EXAMINED')
        
        for province, projects in provinces_with_projects.items():
            # Find experts for this province
            experts = User.objects.filter(
                role='EXPERT',
                phone_number__isnull=False
            ).exclude(phone_number='')
            
            for expert in experts:
                # Check if we already sent a notification to this expert recently
                recent_log = SMSLog.objects.filter(
                    recipient_user=expert,
                    message__contains='بررسی نشده',
                    sent_at__gte=timezone.now() - timedelta(days=1)  # Within last day
                ).exists()
                
                if recent_log:
                    continue
                
                project_count = len(projects)
                project_list = ', '.join([p.name[:30] for p in projects[:3]])  # First 3 projects
                if len(projects) > 3:
                    project_list += f" و {len(projects) - 3} پروژه دیگر"
                
                if template:
                    message = template.content.format(
                        expert_name=expert.get_full_name() or expert.username,
                        project_count=project_count,
                        project_list=project_list,
                        days=settings.not_examined_days
                    )
                else:
                    message = f"سلام جناب {expert.get_full_name()}\n" \
                             f"{project_count} پروژه {settings.not_examined_days} روز است که منتظر بررسی شماست:\n" \
                             f"{project_list}\n" \
                             f"لطفاً در اسرع وقت نسبت به بررسی اقدام کنید.\n" \
                             f"(ارسال خودکار سیستم)"
                
                result = IPPanelSMSSender.send_sms(
                    recipient_number=expert.phone_number,
                    message=message,
                    sender_user=None,
                    recipient_user=expert,
                    template=template
                )
                
                if result['status'] == 'OK':
                    sent_count += 1
                    self.stdout.write(
                        f"✓ Sent examination reminder to expert {expert.username} "
                        f"for {project_count} projects in {province}"
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(
                            f"✗ Failed to send to expert {expert.username}: {result['message']}"
                        )
                    )
        
        self.stdout.write(f"Sent {sent_count} examination reminder notifications")
        return sent_count 