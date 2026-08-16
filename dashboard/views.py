from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.db.models import Sum, Count, Avg, Q, F, Value
from django.db.models.functions import Coalesce
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.db import models

from creator_project.models import Project, ALL_Project
from creator_program.models import Program
from creator_subproject.models import SubProject, SituationReport
# Comment out the missing import and use a placeholder
# from creator_review.models import ProjectReview, SubProjectReview
from accounts.models import User
from .models import SecuritySettings


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

    context = {
        'user': request.user,
        'users_count': users_count,
        'security_settings': security_settings,
    }
    
    return render(request, 'dashboard/admin_dashboard.html', context)


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
