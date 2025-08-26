from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.http import HttpRequest
from django.db import transaction
from .models import (
    ActivityLog, ProjectChangeLog, UserSession, SystemEvent, 
    ActivityDashboard, AuditTrail
)
import json
import traceback
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta


def get_client_ip(request: HttpRequest) -> str:
    """Extract client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def log_activity(
    activity_type: str,
    description: str,
    user = None,
    request: Optional[HttpRequest] = None,
    content_object: Optional[Any] = None,
    details: Optional[Dict[str, Any]] = None,
    severity: str = 'LOW',
    is_system_event: bool = False
) -> ActivityLog:
    """
    Log a general activity
    """
    try:
        # Extract request information
        ip_address = None
        user_agent = None
        session_key = None
        
        if request:
            ip_address = get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            session_key = request.session.session_key if request.session else None
        
        # Get content type and object id if content_object is provided
        content_type = None
        object_id = None
        if content_object:
            content_type = ContentType.objects.get_for_model(content_object)
            object_id = content_object.pk
        
        # Create the activity log
        activity_log = ActivityLog.objects.create(
            user=user,
            activity_type=activity_type,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
            session_key=session_key,
            content_type=content_type,
            object_id=object_id,
            details=details or {},
            severity=severity,
            is_system_event=is_system_event
        )
        
        return activity_log
    
    except Exception as e:
        # Log the error to prevent infinite loops
        print(f"Error logging activity: {e}")
        return None


def get_persian_field_label(field_name: str, model_type: str = 'project') -> str:
    """
    Get Persian field label for a given field name
    """
    field_labels = {
        'project': {
            'name': 'نام پروژه',
            'project_type': 'نوع پروژه',
            'province': 'استان',
            'city': 'شهر',
            'area_size': 'عرصه',
            'site_area': 'مساحت محوطه سازی',
            'wall_length': 'طول دیوار کشی',
            'notables': 'اعیان',
            'floor': 'طبقه',
            'physical_progress': 'پیشرفت فیزیکی',
            'estimated_opening_time': 'تاریخ پایان پروژه',
            'overall_status': 'وضعیت کلی',
            'program': 'طرح',
            'is_approved': 'تایید شده',
            'is_submitted': 'ارسال شده',
            'is_expert_approved': 'تایید کارشناس',
            'allocation_credit_cash_national': 'اعتبار نقدی ملی',
            'allocation_credit_cash_province': 'اعتبار نقدی استانی',
            'allocation_credit_cash_charity': 'اعتبار نقدی خیرین',
            'allocation_credit_cash_travel': 'اعتبار نقدی سفر',
            'allocation_credit_treasury_national': 'اعتبار خزانه ملی',
            'allocation_credit_treasury_province': 'اعتبار خزانه استانی',
            'allocation_credit_treasury_travel': 'اعتبار خزانه سفر',
            'debt': 'دیون',
        },
        'subproject': {
            'sub_project_type': 'نوع زیرپروژه',
            'state': 'وضعیت',
            'physical_progress': 'پیشرفت فیزیکی',
            'remaining_work': 'کار باقیمانده',
            'description': 'توضیحات',
            'contract_amount': 'مبلغ قرارداد',
            'contract_type': 'نوع قرارداد',
            'execution_method': 'روش اجرا',
            'contractor_name': 'نام پیمانکار',
            'contractor_id': 'شناسه پیمانکار',
            'has_adjustment': 'افزایش 25 درصدی قرارداد',
            'adjustment_coefficient': 'درصد افزایش مبلغ قرارداد',
            'imagenary_duration': 'مدت تخمینی',
            'imagenrary_cost': 'هزینه تخمینی',
            'start_date': 'تاریخ شروع',
            'end_date': 'تاریخ پایان',
            'contract_start_date': 'تاریخ شروع قرارداد',
            'contract_end_date': 'تاریخ پایان قرارداد',
            'relationship_delay': 'تاخیر رابطه',
            'relationship_type': 'نوع رابطه',
            'related_subproject_id': 'زیرپروژه مرتبط',
            'transaction_threshold': 'نصاب معاملات',
            'tender_type': 'نوع مناقصه',
            'has_consultant': 'مشاور',
            'consultant_name': 'نام مشاور',
            'consultant_national_id': 'شناسه ملی مشاور',
        },
        'program': {
            'title': 'عنوان طرح',
            'program_id': 'کد طرح',
            'program_type': 'نوع طرح',
            'province': 'استان',
            'city': 'شهر',
            'license_state': 'وضعیت مجوز دفترچه توجیهی',
            'license_code': 'کد مجوز دفترچه توجیهی',
            'address': 'آدرس',
            'longitude': 'طول جغرافیایی',
            'latitude': 'عرض جغرافیایی',
            'description': 'توضیحات',
            'program_opening_date': 'تاریخ افتتاح طرح',
            'is_approved': 'تایید شده',
            'is_submitted': 'ارسال شده',
            'is_expert_approved': 'تایید کارشناس',
        },
        'funding_request': {
            'province_suggested_amount': 'مبلغ پیشنهادی استان',
            'priority': 'اولویت',
            'province_description': 'توضیحات استان',
            'status': 'وضعیت',
            'requested_amount': 'مبلغ درخواستی',
        }
    }
    
    return field_labels.get(model_type, {}).get(field_name, field_name)


def format_field_value(value: str, field_name: str, model_type: str = 'project') -> str:
    """
    Format field value for display with Persian formatting
    """
    if not value:
        return '-'
    
    # Handle boolean values
    if value.lower() in ['true', 'false']:
        return 'بله' if value.lower() == 'true' else 'خیر'
    
    # Handle numeric values with Persian formatting
    if field_name in ['physical_progress', 'adjustment_coefficient']:
        try:
            float_val = float(value)
            return f"{float_val:.1f}%"
        except:
            pass
    
    # Handle currency fields
    currency_fields = [
        'contract_amount', 'imagenrary_cost', 'allocation_credit_cash_national',
        'allocation_credit_cash_province', 'allocation_credit_cash_charity',
        'allocation_credit_cash_travel', 'allocation_credit_treasury_national',
        'allocation_credit_treasury_province', 'allocation_credit_treasury_travel',
        'debt', 'province_suggested_amount', 'requested_amount'
    ]
    if field_name in currency_fields:
        try:
            float_val = float(value)
            return f"{float_val:,.0f} ریال"
        except:
            pass
    
    # Handle date fields
    date_fields = [
        'estimated_opening_time', 'start_date', 'end_date', 
        'contract_start_date', 'contract_end_date', 'program_opening_date'
    ]
    if field_name in date_fields:
        try:
            # Convert to Persian date if possible
            from datetime import datetime
            date_obj = datetime.strptime(value, '%Y-%m-%d')
            return date_obj.strftime('%Y/%m/%d')
        except:
            pass
    
    return value


def log_project_change(
    project_id: str,
    project_name: str,
    change_type: str,
    change_description: str,
    user = None,
    field_name: str = '',
    old_value: Optional[str] = None,
    new_value: Optional[str] = None,
    related_object_type: str = '',
    related_object_id: str = ''
) -> ProjectChangeLog:
    """
    Log a project-specific change with enhanced field information
    """
    try:
        # Get Persian field label
        field_label = get_persian_field_label(field_name, related_object_type.lower() if related_object_type else 'project')
        
        # Format values for display
        formatted_old_value = format_field_value(old_value, field_name, related_object_type.lower() if related_object_type else 'project')
        formatted_new_value = format_field_value(new_value, field_name, related_object_type.lower() if related_object_type else 'project')
        
        project_change = ProjectChangeLog.objects.create(
            user=user,
            project_id=project_id,
            project_name=project_name,
            change_type=change_type,
            field_name=field_label,  # Store Persian label
            original_field_name=field_name,  # Store original field name
            old_value=formatted_old_value,
            new_value=formatted_new_value,
            change_description=change_description,
            related_object_type=related_object_type,
            related_object_id=related_object_id
        )
        
        return project_change
    
    except Exception as e:
        print(f"Error logging project change: {e}")
        return None


def log_system_event(
    event_type: str,
    title: str,
    description: str,
    severity: str = 'LOW',
    component: str = '',
    error_code: str = '',
    stack_trace: str = '',
    details: Optional[Dict[str, Any]] = None
) -> SystemEvent:
    """
    Log a system event or error
    """
    try:
        system_event = SystemEvent.objects.create(
            event_type=event_type,
            title=title,
            description=description,
            severity=severity,
            component=component,
            error_code=error_code,
            stack_trace=stack_trace,
            details=details or {}
        )
        
        return system_event
    
    except Exception as e:
        print(f"Error logging system event: {e}")
        return None


def track_user_session(
    user,
    session_key: str,
    request: HttpRequest
) -> UserSession:
    """
    Track a new user session
    """
    try:
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Close any existing active sessions for this user
        UserSession.objects.filter(
            user=user,
            is_active=True
        ).update(
            is_active=False,
            logout_time=timezone.now()
        )
        
        # Create new session
        session = UserSession.objects.create(
            user=user,
            session_key=session_key,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return session
    
    except Exception as e:
        print(f"Error tracking user session: {e}")
        return None


def update_session_activity(session_key: str) -> bool:
    """
    Update session activity timestamp and page views
    """
    try:
        session = UserSession.objects.get(session_key=session_key, is_active=True)
        session.page_views += 1
        session.last_activity = timezone.now()
        session.save()
        return True
    except UserSession.DoesNotExist:
        return False
    except Exception as e:
        print(f"Error updating session activity: {e}")
        return False


def end_user_session(session_key: str) -> bool:
    """
    End a user session
    """
    try:
        session = UserSession.objects.get(session_key=session_key, is_active=True)
        session.is_active = False
        session.logout_time = timezone.now()
        session.save()
        return True
    except UserSession.DoesNotExist:
        return False
    except Exception as e:
        print(f"Error ending user session: {e}")
        return False


def cleanup_expired_sessions() -> int:
    """
    Clean up expired sessions (sessions that have timed out)
    Returns the number of sessions cleaned up
    """
    try:
        from datetime import timedelta
        
        # Get timeout threshold (15 minutes)
        timeout_threshold = timezone.now() - timedelta(minutes=UserSession.SESSION_TIMEOUT_MINUTES)
        
        # Find expired sessions
        expired_sessions = UserSession.objects.filter(
            is_active=True,
            last_activity__lt=timeout_threshold
        )
        
        # Mark them as inactive
        count = expired_sessions.count()
        expired_sessions.update(
            is_active=False,
            logout_time=timezone.now()
        )
        
        return count
    
    except Exception as e:
        print(f"Error cleaning up expired sessions: {e}")
        return 0


def get_user_online_status(user) -> dict:
    """
    Get detailed online status for a user
    """
    try:
        active_session = UserSession.objects.filter(
            user=user,
            is_active=True
        ).first()
        
        if not active_session:
            return {
                'is_online': False,
                'last_activity': None,
                'session_duration': None,
                'time_since_last_activity': None
            }
        
        return {
            'is_online': active_session.is_online,
            'last_activity': active_session.last_activity,
            'session_duration': active_session.session_duration,
            'time_since_last_activity': active_session.time_since_last_activity,
            'session': active_session
        }
    
    except Exception as e:
        print(f"Error getting user online status: {e}")
        return {
            'is_online': False,
            'last_activity': None,
            'session_duration': None,
            'time_since_last_activity': None
        }


def get_all_online_users() -> list:
    """
    Get all currently online users
    """
    try:
        # Clean up expired sessions first
        cleanup_expired_sessions()
        
        # Get all active sessions that are still online
        online_sessions = UserSession.objects.filter(
            is_active=True
        ).select_related('user')
        
        online_users = []
        for session in online_sessions:
            if session.is_online:
                online_users.append({
                    'user': session.user,
                    'session': session,
                    'last_activity': session.last_activity,
                    'session_duration': session.session_duration,
                    'time_since_last_activity': session.time_since_last_activity
                })
        
        return online_users
    
    except Exception as e:
        print(f"Error getting online users: {e}")
        return []


def create_audit_trail(
    operation: str,
    resource_type: str,
    resource_id: str,
    user = None,
    request: Optional[HttpRequest] = None,
    before_state: Optional[Dict[str, Any]] = None,
    after_state: Optional[Dict[str, Any]] = None,
    requires_approval: bool = False
) -> AuditTrail:
    """
    Create an audit trail entry for sensitive operations
    """
    try:
        ip_address = None
        user_agent = None
        session_id = None
        
        if request:
            ip_address = get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            session_id = request.session.session_key if request.session else None
        
        audit_trail = AuditTrail.objects.create(
            user=user,
            operation=operation,
            resource_type=resource_type,
            resource_id=resource_id,
            before_state=before_state or {},
            after_state=after_state or {},
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            requires_approval=requires_approval
        )
        
        return audit_trail
    
    except Exception as e:
        print(f"Error creating audit trail: {e}")
        return None


def update_daily_dashboard(date: Optional[datetime.date] = None) -> ActivityDashboard:
    """
    Update or create daily dashboard statistics
    """
    if date is None:
        date = timezone.now().date()
    
    try:
        # Get or create dashboard for the date
        dashboard, created = ActivityDashboard.objects.get_or_create(
            date=date,
            defaults={'last_updated': timezone.now()}
        )
        
        # Calculate statistics for the date
        start_datetime = timezone.make_aware(datetime.combine(date, datetime.min.time()))
        end_datetime = timezone.make_aware(datetime.combine(date, datetime.max.time()))
        
        # Activity statistics
        dashboard.total_activities = ActivityLog.objects.filter(
            timestamp__range=(start_datetime, end_datetime)
        ).count()
        
        dashboard.total_logins = ActivityLog.objects.filter(
            timestamp__range=(start_datetime, end_datetime),
            activity_type='LOGIN'
        ).count()
        
        dashboard.total_project_changes = ProjectChangeLog.objects.filter(
            timestamp__range=(start_datetime, end_datetime)
        ).count()
        
        dashboard.total_system_events = SystemEvent.objects.filter(
            timestamp__range=(start_datetime, end_datetime)
        ).count()
        
        # User statistics
        dashboard.active_users = UserSession.objects.filter(
            login_time__range=(start_datetime, end_datetime)
        ).values('user').distinct().count()
        
        # Project statistics (you'll need to adapt these based on your project models)
        # dashboard.projects_created = Project.objects.filter(
        #     created_at__date=date
        # ).count()
        
        # Error statistics
        dashboard.errors_count = SystemEvent.objects.filter(
            timestamp__range=(start_datetime, end_datetime),
            event_type='ERROR'
        ).count()
        
        dashboard.warnings_count = SystemEvent.objects.filter(
            timestamp__range=(start_datetime, end_datetime),
            event_type='WARNING'
        ).count()
        
        dashboard.last_updated = timezone.now()
        dashboard.save()
        
        return dashboard
    
    except Exception as e:
        print(f"Error updating daily dashboard: {e}")
        return None


def get_activity_summary(days: int = 7) -> Dict[str, Any]:
    """
    Get activity summary for the last N days
    """
    try:
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Get daily dashboards
        dashboards = ActivityDashboard.objects.filter(
            date__range=(start_date, end_date)
        ).order_by('date')
        
        # Calculate totals
        total_activities = sum(d.total_activities for d in dashboards)
        total_logins = sum(d.total_logins for d in dashboards)
        total_project_changes = sum(d.total_project_changes for d in dashboards)
        total_errors = sum(d.errors_count for d in dashboards)
        
        # Get recent activities
        recent_activities = ActivityLog.objects.filter(
            timestamp__date__gte=start_date
        ).select_related('user').order_by('-timestamp')[:10]
        
        # Get recent system events
        recent_system_events = SystemEvent.objects.filter(
            timestamp__date__gte=start_date
        ).order_by('-timestamp')[:5]
        
        return {
            'period_days': days,
            'start_date': start_date,
            'end_date': end_date,
            'total_activities': total_activities,
            'total_logins': total_logins,
            'total_project_changes': total_project_changes,
            'total_errors': total_errors,
            'recent_activities': recent_activities,
            'recent_system_events': recent_system_events,
            'daily_data': list(dashboards.values('date', 'total_activities', 'total_logins', 'errors_count'))
        }
    
    except Exception as e:
        print(f"Error getting activity summary: {e}")
        return {}


def cleanup_old_logs(days_to_keep: int = 90) -> Dict[str, int]:
    """
    Clean up old log entries to prevent database bloat
    """
    try:
        cutoff_date = timezone.now() - timedelta(days=days_to_keep)
        
        # Count records to be deleted
        activity_count = ActivityLog.objects.filter(timestamp__lt=cutoff_date).count()
        project_change_count = ProjectChangeLog.objects.filter(timestamp__lt=cutoff_date).count()
        session_count = UserSession.objects.filter(login_time__lt=cutoff_date).count()
        system_event_count = SystemEvent.objects.filter(
            timestamp__lt=cutoff_date,
            is_resolved=True
        ).count()
        
        # Delete old records
        ActivityLog.objects.filter(timestamp__lt=cutoff_date).delete()
        ProjectChangeLog.objects.filter(timestamp__lt=cutoff_date).delete()
        UserSession.objects.filter(login_time__lt=cutoff_date).delete()
        SystemEvent.objects.filter(
            timestamp__lt=cutoff_date,
            is_resolved=True
        ).delete()
        
        return {
            'activities_deleted': activity_count,
            'project_changes_deleted': project_change_count,
            'sessions_deleted': session_count,
            'system_events_deleted': system_event_count
        }
    
    except Exception as e:
        print(f"Error cleaning up old logs: {e}")
        return {}


class ActivityLogger:
    """
    Context manager for logging activities with automatic error handling
    """
    
    def __init__(self, activity_type: str, description: str, **kwargs):
        self.activity_type = activity_type
        self.description = description
        self.kwargs = kwargs
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            # Log the error
            log_system_event(
                event_type='ERROR',
                title=f'Activity logging error: {self.activity_type}',
                description=f'Error occurred while logging activity: {exc_val}',
                severity='MEDIUM',
                component='ActivityMonitor',
                stack_trace=traceback.format_exc()
            )
        else:
            # Log the successful activity
            log_activity(
                activity_type=self.activity_type,
                description=self.description,
                **self.kwargs
            )
