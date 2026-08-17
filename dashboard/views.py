from datetime import timedelta
import os

from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.db.models import Sum, Count, Avg, Q, F, Value
from django.db.models.functions import Coalesce
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.db import models
from django.utils import timezone

from creator_project.models import Project, ALL_Project
from creator_program.models import Program
from creator_subproject.models import SubProject, SituationReport
# Comment out the missing import and use a placeholder
# from creator_review.models import ProjectReview, SubProjectReview
from accounts.models import User
from .models import SecuritySettings
from ai_assistant.models import (
    AIAuditLog, AIConversation, AIMessage, AIPendingAction,
    AIPlatformSettings, AIUsageRecord, AIUserPolicy,
    AIRolePolicy,
)
from ai_assistant.forms import AIPlatformSettingsForm


def _get_province_stats():
    """Build province summaries with their top-level programs."""
    province_stats = list(Project.objects.values('province').annotate(
        total_projects=Count('id'),
        avg_physical_progress=Avg('physical_progress'),
        total_cash_allocation=Sum('allocation_credit_cash_national') +
                             Sum('allocation_credit_cash_province') +
                             Sum('allocation_credit_cash_charity') +
                             Sum('allocation_credit_cash_travel'),
        total_treasury_allocation=Sum('allocation_credit_treasury_national') +
                                 Sum('allocation_credit_treasury_province') +
                                 Sum('allocation_credit_treasury_travel'),
        total_debt=Sum('debt')
    ).order_by('province'))

    programs_by_province = {}
    for program in Program.objects.prefetch_related('projects').order_by('title'):
        programs_by_province.setdefault(program.province, []).append({
            'id': program.id,
            'title': program.title,
            'program_id': program.program_id,
            'program_type': program.program_type,
            'project_count': program.projects.count(),
        })

    # Include provinces that have programs but no projects yet.
    known_provinces = {item['province'] for item in province_stats}
    for province_name in sorted(set(programs_by_province) - known_provinces):
        province_stats.append({
            'province': province_name,
            'total_projects': 0,
            'avg_physical_progress': 0,
            'total_cash_allocation': 0,
            'total_treasury_allocation': 0,
            'total_debt': 0,
        })
    province_stats.sort(key=lambda item: item['province'])

    for province in province_stats:
        province['total_cash_allocation'] = province['total_cash_allocation'] or 0
        province['total_treasury_allocation'] = province['total_treasury_allocation'] or 0
        province['total_debt'] = province['total_debt'] or 0
        province['total_allocation'] = (
            province['total_cash_allocation'] + province['total_treasury_allocation']
        )
        province['programs'] = programs_by_province.get(province['province'], [])
        province['total_programs'] = len(province['programs'])

        if province['total_allocation'] > 0:
            province_projects = Project.objects.filter(province=province['province'])
            total_payments = sum(
                project.get_total_latest_payments() for project in province_projects
            )
            province['avg_financial_progress'] = min(
                100, (total_payments / province['total_allocation']) * 100
            ) if total_payments > 0 else 0
        else:
            province['avg_financial_progress'] = 0

    return province_stats


@login_required
def dashboard_redirect(request):
    """Redirect to appropriate dashboard based on user role."""
    user = request.user
    
    if user.is_admin:
        return redirect('dashboard:admin_dashboard')
    elif user.is_ceo:
        return redirect('dashboard:ceo_dashboard')
    elif user.is_chief_executive:
        return redirect('dashboard:chief_executive_dashboard')
    elif user.is_vice_chief_executive:
        return redirect('dashboard:vice_chief_executive_dashboard')
    elif user.is_expert:
        return redirect('dashboard:expert_dashboard')
    elif user.is_province_manager:
        return redirect('dashboard:province_manager_dashboard')
    else:
        return redirect('accounts:login')


@login_required
def dashboard(request):
    """General dashboard view."""
    user = request.user
    context = {'user': user}
    
    # Redirect to role-specific dashboard
    return dashboard_redirect(request)


@login_required
def admin_dashboard(request):
    """Admin dashboard view."""
    if not request.user.is_admin:
        return HttpResponseForbidden("You don't have permission to access this page.")
    
    users_count = {
        'total': request.user._meta.model.objects.count(),
        'active': request.user._meta.model.objects.filter(is_active=True).count(),
        'admin': request.user._meta.model.objects.filter(role='ADMIN').count(),
        'ceo': request.user._meta.model.objects.filter(role='CEO').count(),
        'chief_executive': request.user._meta.model.objects.filter(role='CHIEF_EXECUTIVE').count(),
        'vice_chief_executive': request.user._meta.model.objects.filter(role='VICE_CHIEF_EXECUTIVE').count(),
        'expert': request.user._meta.model.objects.filter(role='EXPERT').count(),
        'province_manager': request.user._meta.model.objects.filter(role='PROVINCE_MANAGER').count(),
    }
    
    security_settings = SecuritySettings.get_solo()
    today = timezone.localdate()
    month_start = today.replace(day=1)
    ai_settings = AIPlatformSettings.get_solo()
    ai_messages_today = AIMessage.objects.filter(
        role='user', created_at__date=today
    ).count()
    ai_messages_month = AIMessage.objects.filter(
        role='user', created_at__date__gte=month_start
    ).count()
    ai_usage_today = AIUsageRecord.objects.filter(
        created_at__date=today
    ).aggregate(
        requests=Coalesce(Sum('request_count'), 0),
        input_tokens=Coalesce(Sum('input_tokens'), 0),
        output_tokens=Coalesce(Sum('output_tokens'), 0),
    )
    ai_usage_month = AIUsageRecord.objects.filter(
        created_at__date__gte=month_start
    ).aggregate(
        requests=Coalesce(Sum('request_count'), 0),
        input_tokens=Coalesce(Sum('input_tokens'), 0),
        output_tokens=Coalesce(Sum('output_tokens'), 0),
    )
    ai_users = User.objects.filter(
        ai_policy__isnull=False
    ).annotate(
        ai_requests=Count(
            'ai_conversations__messages',
            filter=Q(
                ai_conversations__messages__role='user',
                ai_conversations__messages__created_at__date__gte=month_start,
            ),
            distinct=True,
        )
    ).select_related('ai_policy').order_by('-ai_requests', 'username')[:8]

    context = {
        'user': request.user,
        'users_count': users_count,
        'security_settings': security_settings,
        'ai_settings': ai_settings,
        'ai_messages_today': ai_messages_today,
        'ai_messages_month': ai_messages_month,
        'ai_usage_today': ai_usage_today,
        'ai_usage_month': ai_usage_month,
        'ai_policy_count': AIUserPolicy.objects.count(),
        'ai_enabled_policy_count': AIUserPolicy.objects.filter(is_enabled=True).count(),
        'ai_active_conversations': AIConversation.objects.filter(
            updated_at__date__gte=month_start
        ).count(),
        'ai_pending_actions': AIPendingAction.objects.filter(status='pending').count(),
        'ai_error_count': AIAuditLog.objects.filter(
            status='error', created_at__date__gte=month_start
        ).count(),
        'ai_users': ai_users,
    }
    
    return render(request, 'dashboard/admin_dashboard.html', context)


@login_required
def ai_control_center(request):
    """Dedicated AI operations console for platform administrators."""
    if not request.user.is_admin:
        return HttpResponseForbidden("You don't have permission to access this page.")

    today = timezone.localdate()
    month_start = today.replace(day=1)
    ai_settings = AIPlatformSettings.get_solo()
    month_usage = AIUsageRecord.objects.filter(created_at__date__gte=month_start)
    month_messages = AIMessage.objects.filter(
        role='user', created_at__date__gte=month_start
    )

    users = list(User.objects.filter(is_active=True).select_related('ai_policy').order_by('username'))
    role_labels_fa = {
        'ADMIN': 'مدیر سامانه',
        'CEO': 'مدیرعامل',
        'CHIEF_EXECUTIVE': 'معاون اجرایی',
        'VICE_CHIEF_EXECUTIVE': 'معاون',
        'EXPERT': 'کارشناس',
        'PROVINCE_MANAGER': 'مدیر استان',
    }
    for user in users:
        user.ai_role_label = role_labels_fa.get(user.role, user.get_role_display())
        policy = getattr(user, 'ai_policy', None)
        if policy:
            user.ai_messages_month = month_messages.filter(
                conversation__user=user
            ).count()
            user.ai_tokens_month = month_usage.filter(
                user=user
            ).aggregate(
                total=Coalesce(Sum('input_tokens'), 0) + Coalesce(Sum('output_tokens'), 0)
            )['total'] or 0
        else:
            user.ai_messages_month = 0
            user.ai_tokens_month = 0

    usage_totals = month_usage.aggregate(
        requests=Coalesce(Sum('request_count'), 0),
        input_tokens=Coalesce(Sum('input_tokens'), 0),
        output_tokens=Coalesce(Sum('output_tokens'), 0),
        search_credits=Coalesce(Sum('search_credits'), 0),
        avg_latency=Coalesce(
            Avg('latency_ms'),
            Value(0.0),
            output_field=models.FloatField(),
        ),
    )
    usage_totals['tokens'] = usage_totals['input_tokens'] + usage_totals['output_tokens']

    chart = []
    for offset in range(13, -1, -1):
        day = today - timedelta(days=offset)
        day_usage = AIUsageRecord.objects.filter(created_at__date=day).aggregate(
            requests=Coalesce(Sum('request_count'), 0),
            tokens=Coalesce(Sum('input_tokens'), 0) + Coalesce(Sum('output_tokens'), 0),
        )
        chart.append({
            'label': day.strftime('%b %d'),
            'requests': day_usage['requests'],
            'tokens': day_usage['tokens'],
        })

    role_stats = []
    for role_value, role_label in User.ROLE_CHOICES:
        role_policy, _ = AIRolePolicy.objects.get_or_create(role=role_value)
        role_stats.append({
            'value': role_value,
            'label': role_labels_fa.get(role_value, role_label),
            'count': User.objects.filter(role=role_value, is_active=True).count(),
            'policy': role_policy,
        })

    recent_events = AIAuditLog.objects.select_related('user').order_by('-created_at')[:8]
    context = {
        'ai_settings': ai_settings,
        'ai_provider_ready': bool(
            ai_settings.get_gapgpt_api_key()
            and (ai_settings.provider_endpoint or os.getenv('GAPGPT_API_URL', ''))
        ),
        'settings_form': AIPlatformSettingsForm(instance=ai_settings),
        'users': users,
        'usage_totals': usage_totals,
        'messages_month': month_messages.count(),
        'messages_today': AIMessage.objects.filter(role='user', created_at__date=today).count(),
        'policies_total': AIUserPolicy.objects.count(),
        'policies_enabled': AIUserPolicy.objects.filter(is_enabled=True).count(),
        'errors_month': AIAuditLog.objects.filter(status='error', created_at__date__gte=month_start).count(),
        'pending_actions': AIPendingAction.objects.filter(status='pending').count(),
        'conversations_month': AIConversation.objects.filter(updated_at__date__gte=month_start).count(),
        'chart': chart,
        'chart_max': max([item['requests'] for item in chart] + [1]),
        'role_stats': role_stats,
        'recent_events': recent_events,
        'month_label': today.strftime('%Y/%m'),
    }
    return render(request, 'dashboard/ai_control_center.html', context)


@login_required
@require_POST
def ai_control_action(request):
    """Handle small, auditable controls exposed by the AI console."""
    if not request.user.is_admin:
        return HttpResponseForbidden("You don't have permission to access this page.")

    def number(name, default=0, minimum=0):
        try:
            return max(minimum, int(request.POST.get(name, default)))
        except (TypeError, ValueError):
            return default

    action = request.POST.get('action')
    if action == 'toggle_service':
        settings_obj = AIPlatformSettings.get_solo()
        settings_obj.enabled = request.POST.get('enabled') == '1'
        settings_obj.save(update_fields=['enabled', 'updated_at'])
        messages.success(request, "سرویس هوش مصنوعی فعال شد." if settings_obj.enabled
                         else "سرویس هوش مصنوعی متوقف شد.")
    elif action == 'save_global_limits':
        settings_obj = AIPlatformSettings.get_solo()
        settings_obj.daily_request_limit = number('daily_request_limit')
        settings_obj.monthly_request_limit = number('monthly_request_limit')
        settings_obj.request_timeout_seconds = number('request_timeout_seconds', 60, 1)
        settings_obj.save(update_fields=[
            'daily_request_limit', 'monthly_request_limit',
            'request_timeout_seconds', 'updated_at',
        ])
        messages.success(request, "سقف مصرف سراسری و مهلت پاسخ به‌روزرسانی شد.")
    elif action == 'save_user_policy':
        user = get_object_or_404(User, pk=request.POST.get('user_id'))
        policy, _ = AIUserPolicy.objects.get_or_create(user=user)
        policy.is_enabled = request.POST.get('is_enabled') == '1'
        policy.allow_web_search = request.POST.get('allow_web_search') == '1'
        policy.allow_write_actions = request.POST.get('allow_write_actions') == '1'
        policy.daily_message_limit = number('daily_message_limit', 30)
        policy.monthly_message_limit = number('monthly_message_limit', 500)
        policy.model_name = request.POST.get('model_name', '').strip()[:100]
        if request.POST.get('api_key', '').strip():
            policy.api_key = request.POST['api_key'].strip()
        policy.save()
        messages.success(request, f"سیاست هوش مصنوعی کاربر {user.username} به‌روزرسانی شد.")
    elif action == 'save_role_policy':
        role = request.POST.get('role')
        valid_roles = {value for value, _label in User.ROLE_CHOICES}
        if role not in valid_roles:
            messages.error(request, "نقش کاربری معتبر نیست.")
        else:
            policy, _ = AIRolePolicy.objects.get_or_create(role=role)
            policy.is_enabled = request.POST.get('is_enabled') == '1'
            policy.allow_web_search = request.POST.get('allow_web_search') == '1'
            policy.allow_write_actions = request.POST.get('allow_write_actions') == '1'
            policy.daily_message_limit = number('daily_message_limit', 30)
            policy.monthly_message_limit = number('monthly_message_limit', 500)
            policy.save()
            messages.success(request, f"سیاست هوش مصنوعی نقش {role} به‌روزرسانی شد.")
    elif action == 'save_provider':
        settings_obj = AIPlatformSettings.get_solo()
        form = AIPlatformSettingsForm(request.POST, instance=settings_obj)
        if form.is_valid():
            form.save()
            messages.success(request, "تنظیمات سرویس‌دهنده و API با موفقیت ذخیره شد.")
        else:
            messages.error(request, "تنظیمات سرویس‌دهنده ذخیره نشد؛ فیلدها را بررسی کنید.")
    else:
        messages.error(request, "عملیات درخواستی ناشناخته است.")
    return redirect('dashboard:ai_control_center')


@login_required
@require_POST
def toggle_turnstile(request):
    if not request.user.is_admin:
        return HttpResponseForbidden("You don't have permission to access this page.")

    security_settings = SecuritySettings.get_solo()
    security_settings.turnstile_enabled = request.POST.get('turnstile_enabled') == 'on'
    security_settings.save(update_fields=['turnstile_enabled', 'updated_at'])

    status = 'enabled' if security_settings.turnstile_enabled else 'disabled'
    messages.success(request, f'Cloudflare Turnstile has been {status}.')
    return redirect('dashboard:admin_dashboard')


@login_required
@require_POST
def toggle_ai_platform(request):
    """Enable or disable the AI provider from the administrator dashboard."""
    if not request.user.is_admin:
        return HttpResponseForbidden("You don't have permission to access this page.")

    ai_settings = AIPlatformSettings.get_solo()
    ai_settings.enabled = request.POST.get('ai_enabled') == 'on'
    ai_settings.save(update_fields=['enabled', 'updated_at'])

    status = 'enabled' if ai_settings.enabled else 'disabled'
    messages.success(request, f'AI assistant has been {status}.')
    return redirect('dashboard:admin_dashboard')


@login_required
def ceo_dashboard(request):
    """CEO dashboard view."""
    if not request.user.is_ceo:
        return HttpResponseForbidden("You don't have permission to access this page.")
    
    # Similar to Chief Executive dashboard but with more operational details
    all_projects = ALL_Project.objects.all()
    
    # Projects by status
    projects_by_status = {
        'approved': Project.objects.filter(is_approved=True).count(),
        'pending': Project.objects.filter(is_submitted=True, is_approved=False).count(),
        'draft': Project.objects.filter(is_submitted=False).count(),
    }
    
    # Subprojects by status (using parent project's status)
    subprojects_by_status = {
        'approved': SubProject.objects.filter(project__is_approved=True).count(),
        'pending': SubProject.objects.filter(project__is_submitted=True, project__is_approved=False).count(),
        'draft': SubProject.objects.filter(project__is_submitted=False).count(),
    }
    
    # Provincial statistics
    province_stats = _get_province_stats()
    
    context = {
        'user': request.user,
        'projects_count': all_projects.count(),
        'projects_by_status': projects_by_status,
        'subprojects_by_status': subprojects_by_status,
        'province_stats': province_stats,
    }
    
    return render(request, 'dashboard/ceo_dashboard.html', context)


@login_required
def chief_executive_dashboard(request):
    """Chief Executive dashboard view."""
    if not request.user.is_chief_executive:
        return HttpResponseForbidden("You don't have permission to access this page.")
    
    # Similar to CEO dashboard but with more operational details
    all_projects = ALL_Project.objects.all()
    
    # Projects by status
    projects_by_status = {
        'approved': Project.objects.filter(is_approved=True).count(),
        'pending': Project.objects.filter(is_submitted=True, is_approved=False).count(),
        'draft': Project.objects.filter(is_submitted=False).count(),
    }
    
    # Subprojects by status (using parent project's status)
    subprojects_by_status = {
        'approved': SubProject.objects.filter(project__is_approved=True).count(),
        'pending': SubProject.objects.filter(project__is_submitted=True, project__is_approved=False).count(),
        'draft': SubProject.objects.filter(project__is_submitted=False).count(),
    }
    
    # Provincial statistics
    province_stats = _get_province_stats()
    
    context = {
        'user': request.user,
        'projects_count': all_projects.count(),
        'projects_by_status': projects_by_status,
        'subprojects_by_status': subprojects_by_status,
        'province_stats': province_stats,
    }
    
    return render(request, 'dashboard/chief_executive_dashboard.html', context)


@login_required
def vice_chief_executive_dashboard(request):
    """Vice Chief Executive dashboard view."""
    if not request.user.is_vice_chief_executive:
        return HttpResponseForbidden("You don't have permission to access this page.")
    
    # Projects pending approval
    pending_projects = Project.objects.filter(is_submitted=True, is_approved=False)
    
    context = {
        'user': request.user,
        'pending_projects': pending_projects,
    }
    
    return render(request, 'dashboard/vice_chief_executive_dashboard.html', context)


@login_required
def expert_dashboard(request):
    """
    Display the expert dashboard with projects and subprojects that need review.
    """
    if not request.user.is_expert:
        messages.error(request, 'شما مجوز دسترسی به این صفحه را ندارید.')
        return redirect('home')
    
    # Get projects that need review, limited to the expert's assigned provinces
    provinces = request.user.get_assigned_provinces()

    # If no provinces are returned, fall back to direct province field
    if not provinces and request.user.province:
        provinces = [request.user.province]

    if provinces:
        projects_to_review = Project.objects.filter(is_submitted=True, is_approved=False, province__in=provinces)
    else:
        # No assigned provinces: show nothing to avoid exposing other provinces' projects
        projects_to_review = Project.objects.none()
    
    # Count of projects already reviewed by this expert
    # Since we don't have the review models yet, we'll set this to 0
    reviewed_count = 0
    
    context = {
        'user': request.user,
        'projects_to_review': projects_to_review,
        'projects_to_review_count': projects_to_review.count(),
        'reviewed_count': reviewed_count,
    }
    
    return render(request, 'dashboard/expert_dashboard.html', context)


@login_required
def province_manager_dashboard(request):
    """Province Manager dashboard view."""
    if not request.user.is_province_manager:
        return HttpResponseForbidden("You don't have permission to access this page.")
    
    # Get the user's provinces
    provinces = request.user.get_assigned_provinces()
    
    # If no assigned provinces found via UserProvince, fall back to direct province field
    if not provinces and request.user.province:
        provinces = [request.user.province]
    
    # Filter projects by user's provinces
    if provinces:
        user_projects = Project.objects.filter(
            models.Q(province__in=provinces) | 
            models.Q(created_by=request.user)
        )
    else:
        user_projects = Project.objects.filter(created_by=request.user)
    
    # Get subprojects for the user's projects
    user_subprojects = SubProject.objects.filter(project__in=user_projects)
    
    # Count by status
    projects_by_status = {
        'total': user_projects.count(),
        'approved': user_projects.filter(is_approved=True).count(),
        'pending': user_projects.filter(is_submitted=True, is_approved=False).count(),
        'draft': user_projects.filter(is_submitted=False).count(),
    }
    
    # For subprojects, we use the parent project's status
    subprojects_by_status = {
        'total': user_subprojects.count(),
        'approved': user_subprojects.filter(project__is_approved=True).count(),
        'pending': user_subprojects.filter(project__is_submitted=True, project__is_approved=False).count(),
        'draft': user_subprojects.filter(project__is_submitted=False).count(),
    }
    
    # Get report statistics from the reporter app
    from reporter.models import ProjectReport, SubProjectReport
    
    # Get reports created by this user
    user_project_reports = ProjectReport.objects.filter(created_by=request.user)
    user_subproject_reports = SubProjectReport.objects.filter(created_by=request.user)
    
    # Recent reports (only user's own reports)
    recent_reports = list(user_project_reports.order_by('-created_at')[:3]) + list(user_subproject_reports.order_by('-created_at')[:3])
    recent_reports.sort(key=lambda x: x.created_at, reverse=True)
    recent_reports = recent_reports[:5]
    
    context = {
        'user': request.user,
        'user_projects': user_projects,
        'user_subprojects': user_subprojects,
        'projects_by_status': projects_by_status,
        'subprojects_by_status': subprojects_by_status,
        'recent_reports': recent_reports,
    }
    
    return render(request, 'dashboard/province_manager_dashboard.html', context)
