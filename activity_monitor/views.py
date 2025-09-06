from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, TemplateView
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum
from django.utils import timezone
from django.conf import settings
from datetime import datetime, timedelta
import json
import jdatetime

from .models import (
    ActivityLog, ProjectChangeLog, UserSession, SystemEvent, 
    ActivityDashboard, AuditTrail, GallerySettings
)
from .utils import get_activity_summary, update_daily_dashboard
from .forms import GallerySettingsForm

# Import the custom user model
from django.apps import apps
User = apps.get_model(settings.AUTH_USER_MODEL)


def is_admin_or_monitor(user):
    """Check if user has admin or monitor permissions"""
    return user.is_staff or user.is_superuser or user.is_admin or user.is_ceo or user.is_chief_executive


def parse_persian_date(persian_date_str):
    """
    Parse a Persian date string in the format YYYY/MM/DD and convert to Gregorian date
    """
    if not persian_date_str or not persian_date_str.strip():
        return None
    
    try:
        # Clean the input string and normalize the format
        persian_date_str = persian_date_str.strip()
        
        # Check for different separators and standardize format
        if '-' in persian_date_str:
            parts = persian_date_str.split('-')
        elif '/' in persian_date_str:
            parts = persian_date_str.split('/')
        else:
            return None
            
        if len(parts) != 3:
            return None
            
        year = int(parts[0])
        month = int(parts[1])
        day = int(parts[2])
        
        # Convert using jdatetime
        persian_date = jdatetime.date(year=year, month=month, day=day)
        gregorian_date = persian_date.togregorian()
        
        return gregorian_date
    except (ValueError, IndexError):
        return None


@login_required
@user_passes_test(is_admin_or_monitor)
def activity_dashboard(request):
    """Main activity monitoring dashboard"""
    
    # Get activity summary for the last 7 days
    summary = get_activity_summary(days=7)
    
    # Get recent activities
    recent_activities = ActivityLog.objects.select_related('user').order_by('-timestamp')[:20]
    
    # Get active sessions
    active_sessions = UserSession.objects.filter(is_active=True).select_related('user')[:10]
    
    # Get unresolved system events
    unresolved_events = SystemEvent.objects.filter(is_resolved=False).order_by('-timestamp')[:5]
    
    # Get project changes for today
    today = timezone.now().date()
    today_changes = ProjectChangeLog.objects.filter(
        timestamp__date=today
    ).select_related('user').order_by('-timestamp')[:10]
    
    context = {
        'summary': summary,
        'recent_activities': recent_activities,
        'active_sessions': active_sessions,
        'unresolved_events': unresolved_events,
        'today_changes': today_changes,
        'today': today,
    }
    
    return render(request, 'activity_monitor/dashboard.html', context)


@login_required
@user_passes_test(is_admin_or_monitor)
def activity_logs(request):
    """View for browsing all activity logs"""
    
    # Get filter parameters
    activity_type = request.GET.get('activity_type', '')
    user_id = request.GET.get('user', '')
    severity = request.GET.get('severity', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    search = request.GET.get('search', '')
    
    # Build queryset
    queryset = ActivityLog.objects.select_related('user', 'content_type')
    
    if activity_type:
        queryset = queryset.filter(activity_type=activity_type)
    
    if user_id:
        queryset = queryset.filter(user_id=user_id)
    
    if severity:
        queryset = queryset.filter(severity=severity)
    
    if date_from:
        # Convert Persian date to Gregorian
        gregorian_date_from = parse_persian_date(date_from)
        if gregorian_date_from:
            queryset = queryset.filter(timestamp__date__gte=gregorian_date_from)
    
    if date_to:
        # Convert Persian date to Gregorian
        gregorian_date_to = parse_persian_date(date_to)
        if gregorian_date_to:
            queryset = queryset.filter(timestamp__date__lte=gregorian_date_to)
    
    if search:
        queryset = queryset.filter(
            Q(description__icontains=search) |
            Q(user__username__icontains=search) |
            Q(user__email__icontains=search) |
            Q(ip_address__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(queryset, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    activity_types = ActivityLog.ACTIVITY_TYPES
    severities = ActivityLog._meta.get_field('severity').choices
    users = User.objects.filter(activity_logs__isnull=False).distinct()
    
    context = {
        'page_obj': page_obj,
        'activity_types': activity_types,
        'severities': severities,
        'users': users,
        'filters': {
            'activity_type': activity_type,
            'user_id': user_id,
            'severity': severity,
            'date_from': date_from,
            'date_to': date_to,
            'search': search,
        }
    }
    
    return render(request, 'activity_monitor/activity_logs.html', context)


@login_required
@user_passes_test(is_admin_or_monitor)
def user_activity_report(request):
    """Detailed user activity report showing login times, session duration, etc."""
    
    # Clean up expired sessions first
    from .utils import cleanup_expired_sessions, get_user_online_status
    cleanup_expired_sessions()
    
    # Get all users with their activity information
    users_with_activity = []
    
    for user in User.objects.filter(is_active=True).order_by('username'):
        # Get last login
        last_login_activity = ActivityLog.objects.filter(
            user=user,
            activity_type='LOGIN'
        ).order_by('-timestamp').first()
        
        # Get last activity
        last_activity = ActivityLog.objects.filter(
            user=user
        ).order_by('-timestamp').first()
        
        # Get session statistics
        user_sessions = UserSession.objects.filter(user=user)
        total_sessions = user_sessions.count()
        total_page_views = user_sessions.aggregate(Sum('page_views'))['page_views__sum'] or 0
        
        # Calculate average session duration
        completed_sessions = user_sessions.filter(logout_time__isnull=False)
        if completed_sessions.exists():
            total_duration = sum([
                (session.logout_time - session.login_time).total_seconds()
                for session in completed_sessions
            ])
            avg_duration = total_duration / completed_sessions.count()
        else:
            avg_duration = 0
        
        # Get login counts for different periods
        now = timezone.now()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)
        year_ago = now - timedelta(days=365)
        
        logins_week = ActivityLog.objects.filter(
            user=user,
            activity_type='LOGIN',
            timestamp__gte=week_ago
        ).count()
        
        logins_month = ActivityLog.objects.filter(
            user=user,
            activity_type='LOGIN',
            timestamp__gte=month_ago
        ).count()
        
        logins_year = ActivityLog.objects.filter(
            user=user,
            activity_type='LOGIN',
            timestamp__gte=year_ago
        ).count()
        
        # Get current online status using improved detection
        online_status = get_user_online_status(user)
        active_session = online_status.get('session')
        
        users_with_activity.append({
            'user': user,
            'last_login': last_login_activity.timestamp if last_login_activity else None,
            'last_activity': last_activity.timestamp if last_activity else None,
            'total_sessions': total_sessions,
            'total_page_views': total_page_views,
            'avg_session_duration': avg_duration,
            'logins_week': logins_week,
            'logins_month': logins_month,
            'logins_year': logins_year,
            'active_session': active_session,
            'is_online': online_status['is_online'],
            'time_since_last_activity': online_status['time_since_last_activity'],
            'session_duration': online_status['session_duration'],
        })
    
    # Sort by last activity (most recent first)
    users_with_activity.sort(key=lambda x: x['last_activity'] or timezone.now().replace(year=1900), reverse=True)
    
    # Calculate today's activities
    today = timezone.now().date()
    today_activities = ActivityLog.objects.filter(
        timestamp__date=today
    ).count()
    
    context = {
        'users_with_activity': users_with_activity,
        'total_users': len(users_with_activity),
        'online_users': len([u for u in users_with_activity if u['is_online']]),
        'today_activities': today_activities,
    }
    
    return render(request, 'activity_monitor/user_activity_report.html', context)


@login_required
@user_passes_test(is_admin_or_monitor)
def project_changes(request):
    """View for browsing project change logs with enhanced details"""
    
    # Get filter parameters
    related_object_type = request.GET.get('related_object_type', '')
    province = request.GET.get('province', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Build queryset
    queryset = ProjectChangeLog.objects.select_related('user')
    
    if related_object_type:
        queryset = queryset.filter(related_object_type=related_object_type)
    
    if province:
        # Filter by province - we need to join with the Project model
        from creator_project.models import Project
        project_ids = Project.objects.filter(province=province).values_list('project_id', flat=True)
        queryset = queryset.filter(project_id__in=project_ids)
    
    if date_from:
        # Convert Persian date to Gregorian
        gregorian_date_from = parse_persian_date(date_from)
        if gregorian_date_from:
            queryset = queryset.filter(timestamp__date__gte=gregorian_date_from)
    
    if date_to:
        # Convert Persian date to Gregorian
        gregorian_date_to = parse_persian_date(date_to)
        if gregorian_date_to:
            queryset = queryset.filter(timestamp__date__lte=gregorian_date_to)
    
    # Pagination
    paginator = Paginator(queryset, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    related_object_type_choices = [
        ('Project', 'پروژه'),
        ('SubProject', 'زیرپروژه'),
        ('Program', 'طرح'),
        ('FundingRequest', 'درخواست اعتبار'),
    ]
    
    # Get province choices from Project model
    from creator_project.models import Project
    province_choices = Project.PROVINCE_CHOICES
    
    # Get statistics
    total_changes = queryset.count()
    changes_today = queryset.filter(timestamp__date=timezone.now().date()).count()
    changes_this_week = queryset.filter(timestamp__date__gte=timezone.now().date() - timedelta(days=7)).count()
    
    # Get change type statistics
    change_type_stats = queryset.values('change_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    context = {
        'page_obj': page_obj,
        'related_object_types': related_object_type_choices,
        'province_choices': province_choices,
        'filters': {
            'related_object_type': related_object_type,
            'province': province,
            'date_from': date_from,
            'date_to': date_to,
        },
        'stats': {
            'total_changes': total_changes,
            'changes_today': changes_today,
            'changes_this_week': changes_this_week,
            'change_type_stats': change_type_stats,
        }
    }
    
    return render(request, 'activity_monitor/project_changes.html', context)


@login_required
@user_passes_test(is_admin_or_monitor)
def program_changes(request):
    """View for browsing program/طرح changes"""
    
    # Get filter parameters
    change_type = request.GET.get('change_type', '')
    program_id = request.GET.get('program_id', '')
    user_id = request.GET.get('user', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    search = request.GET.get('search', '')
    
    # Build queryset for program-related activities
    queryset = ActivityLog.objects.filter(
        Q(description__icontains='program') |
        Q(description__icontains='طرح') |
        Q(content_type__model='program')
    ).select_related('user', 'content_type')
    
    if change_type:
        queryset = queryset.filter(activity_type=change_type)
    
    if user_id:
        queryset = queryset.filter(user_id=user_id)
    
    if date_from:
        # Convert Persian date to Gregorian
        gregorian_date_from = parse_persian_date(date_from)
        if gregorian_date_from:
            queryset = queryset.filter(timestamp__date__gte=gregorian_date_from)
    
    if date_to:
        # Convert Persian date to Gregorian
        gregorian_date_to = parse_persian_date(date_to)
        if gregorian_date_to:
            queryset = queryset.filter(timestamp__date__lte=gregorian_date_to)
    
    if search:
        queryset = queryset.filter(
            Q(description__icontains=search) |
            Q(user__username__icontains=search) |
            Q(details__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(queryset, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    change_types = ActivityLog.ACTIVITY_TYPES
    users = User.objects.filter(activity_logs__isnull=False).distinct()
    
    context = {
        'page_obj': page_obj,
        'change_types': change_types,
        'users': users,
        'filters': {
            'change_type': change_type,
            'program_id': program_id,
            'user_id': user_id,
            'date_from': date_from,
            'date_to': date_to,
            'search': search,
        }
    }
    
    return render(request, 'activity_monitor/program_changes.html', context)


@login_required
@user_passes_test(is_admin_or_monitor)
def subproject_changes(request):
    """View for browsing subproject changes"""
    
    # Get filter parameters
    change_type = request.GET.get('change_type', '')
    subproject_id = request.GET.get('subproject_id', '')
    user_id = request.GET.get('user', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    search = request.GET.get('search', '')
    
    # Build queryset for subproject-related activities
    queryset = ActivityLog.objects.filter(
        Q(description__icontains='subproject') |
        Q(description__icontains='زیرپروژه') |
        Q(content_type__model='subproject')
    ).select_related('user', 'content_type')
    
    if change_type:
        queryset = queryset.filter(activity_type=change_type)
    
    if user_id:
        queryset = queryset.filter(user_id=user_id)
    
    if date_from:
        # Convert Persian date to Gregorian
        gregorian_date_from = parse_persian_date(date_from)
        if gregorian_date_from:
            queryset = queryset.filter(timestamp__date__gte=gregorian_date_from)
    
    if date_to:
        # Convert Persian date to Gregorian
        gregorian_date_to = parse_persian_date(date_to)
        if gregorian_date_to:
            queryset = queryset.filter(timestamp__date__lte=gregorian_date_to)
    
    if search:
        queryset = queryset.filter(
            Q(description__icontains=search) |
            Q(user__username__icontains=search) |
            Q(details__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(queryset, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    change_types = ActivityLog.ACTIVITY_TYPES
    users = User.objects.filter(activity_logs__isnull=False).distinct()
    
    context = {
        'page_obj': page_obj,
        'change_types': change_types,
        'users': users,
        'filters': {
            'change_type': change_type,
            'subproject_id': subproject_id,
            'user_id': user_id,
            'date_from': date_from,
            'date_to': date_to,
            'search': search,
        }
    }
    
    return render(request, 'activity_monitor/subproject_changes.html', context)


@login_required
@user_passes_test(is_admin_or_monitor)
def system_events(request):
    """View for browsing system events"""
    
    # Get filter parameters
    event_type = request.GET.get('event_type', '')
    severity = request.GET.get('severity', '')
    component = request.GET.get('component', '')
    is_resolved = request.GET.get('is_resolved', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    search = request.GET.get('search', '')
    
    # Build queryset
    queryset = SystemEvent.objects.select_related('resolved_by')
    
    if event_type:
        queryset = queryset.filter(event_type=event_type)
    
    if severity:
        queryset = queryset.filter(severity=severity)
    
    if component:
        queryset = queryset.filter(component=component)
    
    if is_resolved != '':
        queryset = queryset.filter(is_resolved=is_resolved == 'true')
    
    if date_from:
        queryset = queryset.filter(timestamp__date__gte=date_from)
    
    if date_to:
        queryset = queryset.filter(timestamp__date__lte=date_to)
    
    if search:
        queryset = queryset.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(error_code__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(queryset, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    event_types = SystemEvent.EVENT_TYPES
    severities = SystemEvent._meta.get_field('severity').choices
    components = SystemEvent.objects.values_list('component', flat=True).distinct()
    
    context = {
        'page_obj': page_obj,
        'event_types': event_types,
        'severities': severities,
        'components': components,
        'filters': {
            'event_type': event_type,
            'severity': severity,
            'component': component,
            'is_resolved': is_resolved,
            'date_from': date_from,
            'date_to': date_to,
            'search': search,
        }
    }
    
    return render(request, 'activity_monitor/system_events.html', context)


@login_required
@user_passes_test(is_admin_or_monitor)
def user_sessions(request):
    """View for browsing user sessions"""
    
    # Get filter parameters
    is_active = request.GET.get('is_active', '')
    user_id = request.GET.get('user', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Build queryset
    queryset = UserSession.objects.select_related('user')
    
    if is_active != '':
        queryset = queryset.filter(is_active=is_active == 'true')
    
    if user_id:
        queryset = queryset.filter(user_id=user_id)
    
    if date_from:
        queryset = queryset.filter(login_time__date__gte=date_from)
    
    if date_to:
        queryset = queryset.filter(login_time__date__lte=date_to)
    
    # Pagination
    paginator = Paginator(queryset, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    users = User.objects.filter(sessions__isnull=False).distinct()
    
    context = {
        'page_obj': page_obj,
        'users': users,
        'filters': {
            'is_active': is_active,
            'user_id': user_id,
            'date_from': date_from,
            'date_to': date_to,
        }
    }
    
    return render(request, 'activity_monitor/user_sessions.html', context)


@login_required
@user_passes_test(is_admin_or_monitor)
def audit_trail(request):
    """View for browsing audit trail"""
    
    # Get filter parameters
    operation = request.GET.get('operation', '')
    resource_type = request.GET.get('resource_type', '')
    user_id = request.GET.get('user', '')
    requires_approval = request.GET.get('requires_approval', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    search = request.GET.get('search', '')
    
    # Build queryset
    queryset = AuditTrail.objects.select_related('user', 'approved_by')
    
    if operation:
        queryset = queryset.filter(operation=operation)
    
    if resource_type:
        queryset = queryset.filter(resource_type=resource_type)
    
    if user_id:
        queryset = queryset.filter(user_id=user_id)
    
    if requires_approval != '':
        queryset = queryset.filter(requires_approval=requires_approval == 'true')
    
    if date_from:
        queryset = queryset.filter(timestamp__date__gte=date_from)
    
    if date_to:
        queryset = queryset.filter(timestamp__date__lte=date_to)
    
    if search:
        queryset = queryset.filter(
            Q(resource_id__icontains=search) |
            Q(user__username__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(queryset, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    operations = AuditTrail.objects.values_list('operation', flat=True).distinct()
    resource_types = AuditTrail.objects.values_list('resource_type', flat=True).distinct()
    users = User.objects.filter(audittrail__isnull=False).distinct()
    
    context = {
        'page_obj': page_obj,
        'operations': operations,
        'resource_types': resource_types,
        'users': users,
        'filters': {
            'operation': operation,
            'resource_type': resource_type,
            'user_id': user_id,
            'requires_approval': requires_approval,
            'date_from': date_from,
            'date_to': date_to,
            'search': search,
        }
    }
    
    return render(request, 'activity_monitor/audit_trail.html', context)


@login_required
@user_passes_test(is_admin_or_monitor)
def analytics(request):
    """Analytics and reporting view"""
    
    # Get date range
    days = int(request.GET.get('days', 30))
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    # Get activity summary
    summary = get_activity_summary(days=days)
    
    # Get activity trends
    activity_trends = ActivityLog.objects.filter(
        timestamp__date__range=[start_date, end_date]
    ).values('timestamp__date').annotate(
        count=Count('id')
    ).order_by('timestamp__date')
    
    # Get activity type breakdown
    activity_types = ActivityLog.objects.filter(
        timestamp__date__range=[start_date, end_date]
    ).values('activity_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Get user activity ranking
    user_activity = ActivityLog.objects.filter(
        timestamp__date__range=[start_date, end_date]
    ).values('user__username').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # Get project change trends
    project_changes = ProjectChangeLog.objects.filter(
        timestamp__date__range=[start_date, end_date]
    ).values('change_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Get system events by severity
    system_events = SystemEvent.objects.filter(
        timestamp__date__range=[start_date, end_date]
    ).values('severity').annotate(
        count=Count('id')
    ).order_by('-count')
    
    context = {
        'summary': summary,
        'activity_trends': list(activity_trends),
        'activity_types': list(activity_types),
        'user_activity': list(user_activity),
        'project_changes': list(project_changes),
        'system_events': list(system_events),
        'days': days,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'activity_monitor/analytics.html', context)


@login_required
@user_passes_test(is_admin_or_monitor)
def resolve_system_event(request, event_id):
    """Resolve a system event"""
    if request.method == 'POST':
        event = get_object_or_404(SystemEvent, id=event_id)
        resolution_notes = request.POST.get('resolution_notes', '')
        
        event.is_resolved = True
        event.resolved_by = request.user
        event.resolved_at = timezone.now()
        event.resolution_notes = resolution_notes
        event.save()
        
        messages.success(request, f'System event "{event.title}" has been resolved.')
        return redirect('activity_monitor:system_events')
    
    return HttpResponseForbidden("Invalid request method")


@login_required
@user_passes_test(is_admin_or_monitor)
def approve_audit_trail(request, audit_id):
    """Approve an audit trail entry"""
    if request.method == 'POST':
        audit = get_object_or_404(AuditTrail, id=audit_id)
        
        if audit.requires_approval and not audit.approved_by:
            audit.approved_by = request.user
            audit.approved_at = timezone.now()
            audit.save()
            
            messages.success(request, f'Audit trail for {audit.operation} has been approved.')
        else:
            messages.warning(request, 'This audit trail does not require approval or has already been approved.')
        
        return redirect('activity_monitor:audit_trail')
    
    return HttpResponseForbidden("Invalid request method")


@login_required
@user_passes_test(is_admin_or_monitor)
def api_activity_summary(request):
    """API endpoint for activity summary data"""
    days = int(request.GET.get('days', 7))
    summary = get_activity_summary(days=days)
    
    return JsonResponse(summary)


@login_required
@user_passes_test(is_admin_or_monitor)
def api_recent_activities(request):
    """API endpoint for recent activities"""
    limit = int(request.GET.get('limit', 10))
    activities = ActivityLog.objects.select_related('user').order_by('-timestamp')[:limit]
    
    data = []
    for activity in activities:
        data.append({
            'id': str(activity.id),
            'timestamp': activity.timestamp.isoformat(),
            'user': activity.user.username if activity.user else 'System',
            'activity_type': activity.activity_type,
            'description': activity.description,
            'severity': activity.severity,
        })
    
    return JsonResponse({'activities': data})


@login_required
@user_passes_test(is_admin_or_monitor)
def api_online_status(request):
    """API endpoint for real-time online status updates"""
    try:
        from .utils import get_all_online_users, cleanup_expired_sessions
        
        # Clean up expired sessions
        cleanup_expired_sessions()
        
        # Get all online users
        online_users = get_all_online_users()
        
        # Format response
        online_data = []
        for user_data in online_users:
            online_data.append({
                'user_id': user_data['user'].id,
                'username': user_data['user'].username,
                'last_activity': user_data['last_activity'].isoformat() if user_data['last_activity'] else None,
                'session_duration': str(user_data['session_duration']),
                'time_since_last_activity': str(user_data['time_since_last_activity']),
                'is_online': True
            })
        
        return JsonResponse({
            'success': True,
            'online_users': online_data,
            'total_online': len(online_data),
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@user_passes_test(is_admin_or_monitor)
def api_user_activity_summary(request):
    """API endpoint for user activity summary"""
    try:
        from .utils import get_all_online_users, cleanup_expired_sessions
        
        # Clean up expired sessions
        cleanup_expired_sessions()
        
        # Get online users
        online_users = get_all_online_users()
        
        # Get today's activities
        today = timezone.now().date()
        today_activities = ActivityLog.objects.filter(
            timestamp__date=today
        ).count()
        
        # Get total users
        total_users = User.objects.filter(is_active=True).count()
        
        return JsonResponse({
            'success': True,
            'total_users': total_users,
            'online_users': len(online_users),
            'today_activities': today_activities,
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


class ActivityLogDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """Detail view for activity log"""
    model = ActivityLog
    template_name = 'activity_monitor/activity_log_detail.html'
    context_object_name = 'activity'
    
    def test_func(self):
        return is_admin_or_monitor(self.request.user)


class SystemEventDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """Detail view for system event"""
    model = SystemEvent
    template_name = 'activity_monitor/system_event_detail.html'
    context_object_name = 'event'
    
    def test_func(self):
        return is_admin_or_monitor(self.request.user)


class AuditTrailDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """Detail view for audit trail"""
    model = AuditTrail
    template_name = 'activity_monitor/audit_trail_detail.html'
    context_object_name = 'audit'
    
    def test_func(self):
        return is_admin_or_monitor(self.request.user)


@login_required
@user_passes_test(is_admin_or_monitor)
def gallery_settings(request):
    """View for configuring gallery settings"""
    settings_obj = GallerySettings.get_settings()
    
    if request.method == 'POST':
        form = GallerySettingsForm(request.POST, instance=settings_obj)
        if form.is_valid():
            settings_obj = form.save(commit=False)
            settings_obj.updated_by = request.user
            settings_obj.save()
            
            # Log the settings change
            ActivityLog.objects.create(
                user=request.user,
                activity_type='UPDATE',
                description='تنظیمات گالری بروزرسانی شد',
                details={
                    'settings_changed': list(form.changed_data),
                    'new_values': {field: form.cleaned_data[field] for field in form.changed_data}
                },
                is_system_event=True,
                severity='LOW'
            )
            
            messages.success(request, 'تنظیمات گالری با موفقیت بروزرسانی شد.')
            return redirect('activity_monitor:gallery_settings')
    else:
        form = GallerySettingsForm(instance=settings_obj)
    
    context = {
        'form': form,
        'settings': settings_obj,
        'title': 'تنظیمات گالری تصاویر',
    }
    
    return render(request, 'activity_monitor/gallery_settings.html', context)
