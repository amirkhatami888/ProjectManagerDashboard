from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse, HttpResponse
from .models import Project, ALL_Project, ProjectRejectionComment, ProjectFinancialAllocation, FundingRequest
from .forms import ProjectForm, FundingRequestForm, ExpertFundingReviewForm, ChiefFundingReviewForm, ProjectRejectionForm, ProjectFinancialAllocationForm
from creator_program.models import Program
import jdatetime
from datetime import datetime
import json
from .geo_utils import is_point_in_province
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, FormView, TemplateView, View
from django.views.generic.detail import SingleObjectMixin
from django.urls import reverse_lazy, reverse
from django.utils import timezone
import csv
from django import forms
from django.db import models
import logging
import sys

# Configure logging to handle Unicode
logging.basicConfig(
    level=logging.DEBUG, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@login_required
def project_list(request):
    # If user is admin, CEO, or chief executive, show all projects
    if request.user.is_admin or request.user.is_ceo or request.user.is_chief_executive:
        projects = Project.objects.all()
    # If user is expert, show submitted projects for their assigned provinces
    elif request.user.is_expert:
        # Get the provinces this expert is assigned to
        assigned_provinces = request.user.get_assigned_provinces()
        
        # If the expert has assigned provinces, filter projects by those provinces
        if assigned_provinces:
            projects = Project.objects.filter(
                is_submitted=True, 
                province__in=assigned_provinces
            )
        else:
            # If no provinces assigned, don't show any projects
            projects = Project.objects.none()
    # If user is vice chief executive, show submitted projects
    elif request.user.is_vice_chief_executive:
        projects = Project.objects.filter(is_submitted=True)
    # If user is province manager or a regular user
    elif request.user.is_province_manager or request.user.province:
        # Get the user's provinces
        provinces = request.user.get_assigned_provinces()
        
        # If no assigned provinces found via UserProvince, fall back to direct province field
        if not provinces and request.user.province:
            provinces = [request.user.province]
        
        # Show projects in the user's province, including their own projects
        if provinces:
            projects = Project.objects.filter(
                models.Q(province__in=provinces) | 
                models.Q(created_by=request.user)
            )
        else:
            projects = Project.objects.none()
    else:
        return HttpResponseForbidden("You don't have permission to view projects.")
    
    return render(request, 'creator_project/project_list.html', {
        'projects': projects,
        'debug': True
    })

@login_required
def expert_all_projects(request):
    """View for experts to see all projects from their assigned provinces, even those not submitted for approval."""
    # Only allow expert users to access this view
    if not request.user.is_expert:
        return HttpResponseForbidden("Only expert users can access this page.")
    
    # Get the provinces this expert is assigned to
    assigned_provinces = request.user.get_assigned_provinces()
    
    # If the expert has assigned provinces, filter projects by those provinces
    if assigned_provinces:
        projects = Project.objects.filter(province__in=assigned_provinces)
    else:
        # If no provinces assigned, don't show any projects
        projects = Project.objects.none()
    
    return render(request, 'creator_project/expert_all_projects.html', {
        'projects': projects,
        'title': 'تمام پروژه‌ها',
        'debug': True
    })

@login_required
def expert_all_programs(request):
    """View for experts to see all programs from their assigned provinces."""
    # Only allow expert users to access this view
    if not request.user.is_expert:
        return HttpResponseForbidden("Only expert users can access this page.")
    
    # Get the provinces this expert is assigned to
    assigned_provinces = request.user.get_assigned_provinces()
    
    # If the expert has assigned provinces, filter programs by those provinces
    if assigned_provinces:
        programs = Program.objects.filter(province__in=assigned_provinces)
    else:
        # If no provinces assigned, don't show any programs
        programs = Program.objects.none()
    
    return render(request, 'creator_project/expert_all_programs.html', {
        'programs': programs,
        'title': 'تمام طرح‌های استان‌های تحت نظارت',
        'debug': True
    })

@login_required
def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    
    # Check permissions
    if not (request.user.is_admin or request.user.is_ceo or request.user.is_chief_executive or 
            request.user.is_vice_chief_executive or request.user.is_expert or 
            (request.user.is_province_manager and project.created_by == request.user)):
        return HttpResponseForbidden("You don't have permission to view this project.")
    
    subprojects = project.get_all_subprojects()
    allocations = project.allocations.all().order_by('-allocation_date')
    
    context = {
        'project': project,
        'subprojects': subprojects,
        'allocations': allocations,
    }
    
    return render(request, 'creator_project/project_detail.html', context)

@login_required
def project_create(request):
    # Only province managers can create projects
    if not request.user.is_province_manager:
        return HttpResponseForbidden("Only province managers can create projects.")
    
    # Check if program_id is provided in the URL parameters
    program_id = request.GET.get('program')
    if not program_id:
        messages.warning(request, "برای ایجاد پروژه، باید از صفحه جزئیات طرح اقدام کنید.")
        return redirect('creator_program:program_list')
    
    # Get the program
    from creator_program.models import Program
    try:
        program = Program.objects.get(id=program_id)
        # Check if the user has permission to create projects under this program
        if program.created_by != request.user and not request.user.is_admin:
            messages.error(request, "شما اجازه ایجاد پروژه برای این طرح را ندارید.")
            return redirect('creator_program:program_list')
    except Program.DoesNotExist:
        messages.error(request, "طرح مورد نظر یافت نشد.")
        return redirect('creator_program:program_list')
    
    # Use logging instead of print for better Unicode handling
    logger.debug(f"User attempting to create project: {request.user.username}")
    logger.debug(f"User role: {request.user.role}")
    
    # Safely log the province with explicit encoding
    try:
        user_provinces = request.user.get_assigned_provinces()
        province = user_provinces[0] if user_provinces else "N/A"
        logger.debug(f"User assigned provinces: {user_provinces}")
        logger.debug(f"User province (repr): {repr(province)}")
    except Exception as e:
        logger.error(f"Error logging province: {e}", exc_info=True)
    
    logger.debug(f"Is province manager: {request.user.is_province_manager}")
    
    if request.method == 'POST':
        # Make a copy to modify if needed
        post_data = request.POST.copy()
        
        # Always set the program field to the one from the URL
        post_data['program'] = program.id
        
        # Set province and city from the program since they are disabled in the form
        post_data['province'] = program.province
        post_data['city'] = program.city or ''
        
        # Set default values for required fields that might not be in the form
        if 'physical_progress' not in post_data or not post_data['physical_progress']:
            post_data['physical_progress'] = '0'
        if 'overall_status' not in post_data or not post_data['overall_status']:
            post_data['overall_status'] = 'غیره فعال'
        
        # Extract and remove estimated_opening_time from form data to prevent validation errors
        persian_date = post_data.get('estimated_opening_time', '')
        if 'estimated_opening_time' in post_data:
            post_data.pop('estimated_opening_time')
            
        # Process the form data without the date field
        form = ProjectForm(post_data, user=request.user)
        
        if form.is_valid():
            print("DEBUG: Form is valid")
            try:
                project = form.save(commit=False)
                project.created_by = request.user
                
                # Set default values for financial fields
                project.allocation_credit_cash_national = 0
                project.allocation_credit_cash_province = 0
                project.allocation_credit_cash_charity = 0
                project.allocation_credit_cash_travel = 0
                project.allocation_credit_treasury_national = 0
                project.allocation_credit_treasury_province = 0
                project.allocation_credit_treasury_travel = 0
                project.debt = 0
            
                # Ensure province is set to the user's assigned province if they are a province manager
                if request.user.is_province_manager:
                    user_provinces = request.user.get_assigned_provinces()
                    if user_provinces:
                        project.province = user_provinces[0]  # Use the first assigned province
                        print(f"DEBUG: Setting project province to {project.province}")
                
                # Convert Persian date manually and set it directly to the instance
                if persian_date and persian_date.strip():
                    try:
                        # Convert Persian digits to English digits if necessary
                        persian_digits = '۰۱۲۳۴۵۶۷۸۹'
                        english_digits = '0123456789'
                        translation_table = str.maketrans(persian_digits, english_digits)
                        persian_date_en = persian_date.translate(translation_table)
                        
                        # Parse Persian date (format: YYYY/MM/DD)
                        parts = persian_date_en.split('/')
                        if len(parts) == 3:
                            j_date = jdatetime.date(int(parts[0]), int(parts[1]), int(parts[2]))
                            gregorian_date = j_date.togregorian()
                            print(f"DEBUG: Converted date {persian_date} to {gregorian_date}")
                            project.estimated_opening_time = gregorian_date
                        else:
                            print(f"DEBUG: Invalid date format: {persian_date_en}")
                            project.estimated_opening_time = None
                    except Exception as e:
                        print(f"DEBUG: Error converting date: {str(e)}")
                        # Don't fail - just leave the date as None
                        project.estimated_opening_time = None
                else:
                    # Clear the date if it was empty
                    project.estimated_opening_time = None
                    print("DEBUG: No date provided, setting to None")
                
                project.save()
                messages.success(request, "پروژه با موفقیت ایجاد شد.")
                return redirect('creator_project:project_detail', pk=project.pk)
            except Exception as e:
                print(f"DEBUG: Error saving project: {str(e)}")
                messages.error(request, f"خطا در ایجاد پروژه: {str(e)}")
        else:
            print("DEBUG: Form is invalid")
            print(f"DEBUG: Form errors: {form.errors}")
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"خطا در فیلد {field}: {error}")
    else:
        # Pre-select the program from the URL parameter and set province/city from program
        initial_data = {
            'program': program.id,
            'province': program.province,
            'city': program.city or '',
            'physical_progress': '0',
            'overall_status': 'غیره فعال'
        }
        form = ProjectForm(user=request.user, initial=initial_data)
        # Make the program field read-only
        form.fields['program'].widget.attrs['readonly'] = True
        form.fields['program'].widget.attrs['disabled'] = True
    
    return render(request, 'creator_project/project_form.html', {
        'form': form, 
        'is_create': True,
        'debug': True,
        'program': program  # Pass the program to the template
    })

@login_required
def project_update(request, pk):
    project = get_object_or_404(Project, pk=pk)
    
    # Check if user has permission to update this project
    if request.user.is_admin:
        # Admins can update any project
        pass
    elif request.user.is_province_manager and project.created_by == request.user:
        # Province managers can only update their own projects
        # Ensure the project belongs to the manager's assigned provinces
        user_provinces = request.user.get_assigned_provinces()
        if user_provinces and project.province not in user_provinces:
            return HttpResponseForbidden("You can only update projects in your assigned provinces.")
    else:
        return HttpResponseForbidden("You don't have permission to update this project.")
    
    if request.method == 'POST':
        # Make a copy to modify if needed
        post_data = request.POST.copy()
        
        # Extract and remove estimated_opening_time from form data to prevent validation errors
        persian_date = post_data.get('estimated_opening_time', '')
        if 'estimated_opening_time' in post_data:
            post_data.pop('estimated_opening_time')
            
        # Process the form data without the date field
        form = ProjectForm(post_data, instance=project, user=request.user)
        print(f"DEBUG: Form data: {post_data}")
        
        if form.is_valid():
            print("DEBUG: Form is valid")
            try:
                # Set the current user as the updater to track in history
                project._update_user = request.user
                
                # Ensure province managers can't change the province
                if request.user.is_province_manager:
                    user_provinces = request.user.get_assigned_provinces()
                    if user_provinces:
                        form.instance.province = user_provinces[0]  # Use the first assigned province
                    
                    # Reset approval status when province manager updates project
                    form.instance.is_submitted = False
                    form.instance.is_expert_approved = False
                    form.instance.is_approved = False
                
                # Don't save the form yet
                project_instance = form.save(commit=False)
                
                # Convert Persian date manually and set it directly to the instance
                if persian_date and persian_date.strip():
                    try:
                        # Convert Persian digits to English digits if necessary
                        import re
                        persian_digits = '۰۱۲۳۴۵۶۷۸۹'
                        english_digits = '0123456789'
                        translation_table = str.maketrans(persian_digits, english_digits)
                        persian_date_en = persian_date.translate(translation_table)
                        
                        # Parse Persian date (format: YYYY/MM/DD)
                        parts = persian_date_en.split('/')
                        if len(parts) == 3:
                            j_date = jdatetime.date(int(parts[0]), int(parts[1]), int(parts[2]))
                            gregorian_date = j_date.togregorian()
                            print(f"DEBUG: Converted date {persian_date} to {gregorian_date}")
                            project_instance.estimated_opening_time = gregorian_date
                        else:
                            print(f"DEBUG: Invalid date format: {persian_date_en}")
                            project_instance.estimated_opening_time = None
                    except Exception as e:
                        print(f"DEBUG: Error converting date: {str(e)}")
                        # Don't fail - just leave the date as None
                        project_instance.estimated_opening_time = None
                else:
                    # Clear the date if it was empty
                    project_instance.estimated_opening_time = None
                
                # Now save the instance with the manually set date
                project_instance.save()
                
                messages.success(request, "پروژه با موفقیت به‌روزرسانی شد.")
                return redirect('creator_project:project_detail', pk=project.pk)
            except Exception as e:
                print(f"DEBUG: Error saving project: {str(e)}")
                messages.error(request, f"خطا در به‌روزرسانی پروژه: {str(e)}")
        else:
            print("DEBUG: Form is invalid")
            print(f"DEBUG: Form errors: {form.errors}")
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"خطا در فیلد {field}: {error}")
    else:
        form = ProjectForm(instance=project, user=request.user)
    
    return render(request, 'creator_project/project_form.html', {
        'form': form, 
        'project': project, 
        'is_create': False,
        'debug': True
    })

@login_required
def project_delete(request, pk):
    project = get_object_or_404(Project, pk=pk)
    
    # Only admins or the project creator can delete projects
    if not (request.user.is_admin or project.created_by == request.user):
        return HttpResponseForbidden("You don't have permission to delete this project.")
    
    # Placeholder for actual implementation
    return render(request, 'creator_project/project_confirm_delete.html', {'project': project})

@login_required
def project_submit(request, pk):
    project = get_object_or_404(Project, pk=pk)
    
    # Only the project creator can submit projects
    if project.created_by != request.user:
        return HttpResponseForbidden("You don't have permission to submit this project.")
    
    # Update project status
    project.is_submitted = True
    # Set the current user as the updater to track in history
    project._update_user = request.user
    project.save()
    
    messages.success(request, "پروژه با موفقیت برای بررسی ارسال شد.")
    return redirect('creator_project:project_detail', pk=project.pk)

@login_required
def project_approve(request, pk):
    project = get_object_or_404(Project, pk=pk)
    
    # Handle approval based on user role
    if request.user.is_expert:
        # Check if expert is assigned to this project's province
        if not request.user.has_province_access(project.province):
            return HttpResponseForbidden("You don't have permission to approve projects from this province.")
            
        # Expert approval - mark as expert approved and fully approved
        project.is_expert_approved = True
        project.is_approved = True  # Now expert directly approves without needing vice approval
        # Set the current user as the updater to track in history
        project._update_user = request.user
        project.save()
        
        # Clear rejection comments when project is approved
        from creator_project.models import ProjectRejectionComment
        ProjectRejectionComment.objects.filter(project=project).delete()
        
        messages.success(request, "پروژه با موفقیت توسط کارشناس تایید نهایی شد.")
        
    elif request.user.is_vice_chief_executive:
        # Vice chief executive approval - if already expert approved, fully approve
        if project.is_expert_approved:
            project.is_approved = True
            # Set the current user as the updater to track in history
            project._update_user = request.user
            project.save()
            
            # Clear rejection comments when project is approved
            from creator_project.models import ProjectRejectionComment
            ProjectRejectionComment.objects.filter(project=project).delete()
            
            messages.success(request, "پروژه با موفقیت تایید نهایی شد.")
        else:
            messages.warning(request, "این پروژه هنوز توسط کارشناس تایید نشده است.")
            
    elif request.user.is_admin:
        # Admin can fully approve regardless of expert approval
        project.is_expert_approved = True
        project.is_approved = True
        # Set the current user as the updater to track in history
        project._update_user = request.user
        project.save()
        
        # Clear rejection comments when project is approved
        from creator_project.models import ProjectRejectionComment
        ProjectRejectionComment.objects.filter(project=project).delete()
        
        messages.success(request, "پروژه با موفقیت تایید شد.")
    else:
        return HttpResponseForbidden("You don't have permission to approve projects.")
        
    return redirect('creator_project:project_detail', pk=project.pk)

@login_required
def project_reject(request, pk):
    project = get_object_or_404(Project, pk=pk)
    
    # Check permissions based on user role
    if request.user.is_admin:
        # Admin can reject any project
        pass
    elif request.user.is_expert:
        # Check if expert is assigned to this project's province
        if not request.user.has_province_access(project.province):
            return HttpResponseForbidden("You don't have permission to reject projects from this province.")
    elif request.user.is_vice_chief_executive:
        # Vice chief can reject any project
        pass
    else:
        return HttpResponseForbidden("You don't have permission to reject projects.")
    
    if request.method == 'POST':
        form = ProjectRejectionForm(request.POST)
        if form.is_valid():
            # Create rejection comment with default field_name
            ProjectRejectionComment.objects.create(
                project=project,
                expert=request.user,
                field_name='other',  # Default to 'other' since we don't collect this anymore
                comment=form.cleaned_data['comment']
            )
            
            # Update project status
            project.is_submitted = False
            # Set the current user as the updater to track in history
            project._update_user = request.user
            # Clear all previous rejection comments when changing to draft status
            project.save()
            
            messages.success(request, "پروژه با موفقیت رد شد.")
            return redirect('creator_project:project_detail', pk=project.pk)
        else:
            messages.error(request, "لطفاً دلیل رد پروژه را وارد کنید.")
    else:
        form = ProjectRejectionForm()
    
    return render(request, 'creator_project/project_reject_form.html', {'form': form, 'project': project})

@login_required
def project_financials(request, pk):
    project = get_object_or_404(Project, pk=pk)
    
    # Check permissions
    if not (request.user.is_admin or request.user.is_expert or 
            (request.user.is_province_manager and project.created_by == request.user)):
        return HttpResponseForbidden("You don't have permission to view project financials.")
    
    # Fetch all financial data
    # This is a placeholder for actual implementation
    return render(request, 'creator_project/project_financials.html', {'project': project})

@login_required
def project_add_allocation(request, pk):
    project = get_object_or_404(Project, pk=pk)
    
    # Check if user has permission to add allocation to this project
    if request.user.is_admin:
        # Admins can add allocation to any project
        pass
    elif request.user.is_expert:
        # Experts can add allocation to any project
        pass
    elif request.user.is_province_manager and project.created_by == request.user:
        # Province managers can only add allocation to their own projects
        # Ensure the project belongs to the manager's assigned provinces
        user_provinces = request.user.get_assigned_provinces()
        if user_provinces and project.province not in user_provinces:
            return HttpResponseForbidden("You can only add allocation to projects in your assigned provinces.")
    else:
        return HttpResponseForbidden("You don't have permission to add allocation to this project.")
    
    if request.method == 'POST':
        form = ProjectFinancialAllocationForm(request.POST)
        
        # Handle Persian date conversion
        if form.is_valid():
            allocation = form.save(commit=False)
            allocation.project = project
            
            # Handle Persian date for allocation_date
            allocation_date = form.cleaned_data.get('allocation_date')
            if allocation_date:
                allocation.allocation_date = allocation_date
            else:
                # Set default date to today if not provided
                allocation.allocation_date = timezone.now().date()
            
            allocation.save()
            
            # Reset approval status if province manager adds allocation
            if request.user.is_province_manager:
                project.is_submitted = False
                project.is_expert_approved = False
                project.is_approved = False
                project.save()
                
            messages.success(request, "تخصیص مالی با موفقیت اضافه شد.")
            
            if 'save_and_add' in request.POST:
                return redirect('creator_project:project_add_allocation', pk=project.pk)
            else:
                return redirect('creator_project:project_detail', pk=project.pk)
    else:
        form = ProjectFinancialAllocationForm()
    
    return render(request, 'creator_project/allocation_form.html', {
        'form': form,
        'project': project
    })

def validate_coordinates(request):
    """AJAX view to validate coordinates for a province."""
    # REMOVED: Coordinate validation function
    return JsonResponse({
        'valid': True,
        'message': 'مختصات پذیرفته شد.'
    })

@login_required
def get_program_details(request):
    """AJAX view to get program details for auto-populating province and city"""
    if request.method == 'GET':
        program_id = request.GET.get('program_id')
        if program_id:
            try:
                program = Program.objects.get(id=program_id)
                return JsonResponse({
                    'success': True,
                    'province': program.province,
                    'city': program.city or ''
                })
            except Program.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'Program not found'
                }, status=404)
        else:
            return JsonResponse({
                'success': False,
                'error': 'Program ID is required'
            }, status=400)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

# Funding Request Views
class FundingRequestListView(LoginRequiredMixin, ListView):
    """List view for funding requests based on user role"""
    model = FundingRequest
    template_name = 'creator_project/funding_request_list.html'
    context_object_name = 'funding_requests'
    paginate_by = 10
    
    def get_queryset(self):
        # Restrict access for province managers and experts
        if self.request.user.is_province_manager or self.request.user.is_expert:
            # Province managers and experts can only see their own or related funding requests
            provinces = self.request.user.get_assigned_provinces()
            
            # If no assigned provinces found via UserProvince, fall back to direct province field
            if not provinces and self.request.user.province:
                provinces = [self.request.user.province]
            
            if provinces:
                queryset = FundingRequest.objects.filter(
                    models.Q(project__province__in=provinces) | 
                    models.Q(created_by=self.request.user)
                )
            else:
                queryset = FundingRequest.objects.filter(created_by=self.request.user)
        
        # Admin and chief users see all requests
        elif self.request.user.is_admin or self.request.user.is_ceo or self.request.user.is_chief_executive:
            queryset = FundingRequest.objects.all()
        
        # Specific status filtering
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_role'] = self.request.user.role
        context['status_filter'] = self.request.GET.get('status', '')
        
        # Add counts for different statuses
        user = self.request.user
        base_queryset = FundingRequest.objects.all()
        
        if user.is_province_manager:
            provinces = user.get_assigned_provinces()
            
            # If no assigned provinces found via UserProvince, fall back to direct province field
            if not provinces and user.province:
                provinces = [user.province]
            
            if provinces:
                base_queryset = base_queryset.filter(project__province__in=provinces)
            else:
                base_queryset = base_queryset.none()
        elif user.is_expert:
            provinces = user.get_assigned_provinces()
            base_queryset = base_queryset.filter(
                models.Q(project__province__in=provinces) | 
                models.Q(expert_user=user)
            )
            
        context['draft_count'] = base_queryset.filter(status='پیش‌نویس').count()
        context['pending_expert_count'] = base_queryset.filter(status='ارسال شده به کارشناس').count()
        context['rejected_by_expert_count'] = base_queryset.filter(status='رد شده توسط کارشناس').count()
        context['pending_chief_count'] = base_queryset.filter(status='ارسال شده به رئیس').count()
        context['rejected_by_chief_count'] = base_queryset.filter(status='رد شده توسط رئیس').count()
        context['approved_count'] = base_queryset.filter(status='تایید شده').count()
        context['archived_count'] = base_queryset.filter(status='در تاریخچه').count()
            
        return context


class FundingRequestCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Create a new funding request"""
    model = FundingRequest
    form_class = FundingRequestForm
    template_name = 'creator_project/funding_request_form.html'
    success_url = reverse_lazy('creator_project:funding_request_list')
    
    def test_func(self):
        # Only province managers can create funding requests
        if hasattr(self.request.user, 'is_province_manager') and self.request.user.is_province_manager:
            project_id = self.request.GET.get('project')
            if project_id:
                try:
                    project = Project.objects.get(pk=project_id)
                    # Allow province managers to create requests for any projects in their province
                    # Not just approved ones
                    user_provinces = self.request.user.get_assigned_provinces()
                    if not user_provinces and self.request.user.province:
                        user_provinces = [self.request.user.province]
                        
                    return project.province in user_provinces
                except Project.DoesNotExist:
                    pass
                    
            return True  # Allow access to form without project preselected
            
        return False
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        
        # Pre-select project if provided in URL
        project_id = self.request.GET.get('project')
        if project_id:
            try:
                project = Project.objects.get(pk=project_id)
                if 'initial' not in kwargs:
                    kwargs['initial'] = {}
                kwargs['initial']['project'] = project.id
            except Project.DoesNotExist:
                pass
                
        return kwargs
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'درخواست اعتبار با موفقیت ایجاد شد.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'ایجاد درخواست اعتبار'
        context['submit_text'] = 'ایجاد درخواست'
        return context


class FundingRequestUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Update an existing funding request"""
    model = FundingRequest
    form_class = FundingRequestForm
    template_name = 'creator_project/funding_request_form.html'
    success_url = reverse_lazy('creator_project:funding_request_list')
    
    def test_func(self):
        # Only the creator can update the request, and only if it's in draft or rejected state
        funding_request = self.get_object()
        user = self.request.user
        
        # Province users can only edit their own draft requests or ones rejected by expert or chief
        if user.is_province_manager:
            return (
                funding_request.created_by == user and 
                (funding_request.status == 'پیش‌نویس' or 
                 funding_request.status == 'رد شده توسط کارشناس')
            )
        
        # Experts can only edit their assigned requests rejected by chief
        if user.is_expert:
            return (
                funding_request.expert_user == user and 
                funding_request.status == 'رد شده توسط رئیس'
            )
            
        return False
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        form.instance.updated_at = timezone.now()
        
        messages.success(self.request, 'درخواست اعتبار با موفقیت بروزرسانی شد.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'ویرایش درخواست اعتبار'
        context['submit_text'] = 'بروزرسانی درخواست'
        return context


class FundingRequestDetailView(LoginRequiredMixin, DetailView):
    """Detail view for a funding request"""
    model = FundingRequest
    template_name = 'creator_project/funding_request_detail.html'
    context_object_name = 'funding_request'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        funding_request = self.get_object()
        
        # Add flags to determine if current user can submit/approve the request
        context['can_submit'] = (
            user.is_province_manager and 
            funding_request.created_by == user and 
            funding_request.status == 'پیش‌نویس'
        )
        
        context['can_expert_review'] = (
            user.is_expert and 
            (user == funding_request.expert_user or not funding_request.expert_user) and
            funding_request.status == 'ارسال شده به کارشناس'
        )
        
        context['can_chief_review'] = (
            user.is_chief_executive and 
            funding_request.status == 'ارسال شده به رئیس'
        )
        
        return context


class SubmitToExpertView(LoginRequiredMixin, UserPassesTestMixin, SingleObjectMixin, FormView):
    """View to submit a funding request to an expert"""
    model = FundingRequest
    template_name = 'creator_project/funding_request_submit.html'
    form_class = forms.Form  # Empty form, just for confirmation
    
    def test_func(self):
        # Only the creator can submit the request, and only if it's in draft state
        funding_request = self.get_object()
        user = self.request.user
        
        return (
            user.is_province_manager and 
            funding_request.created_by == user and 
            funding_request.status == 'پیش‌نویس'
        )
    
    def get_success_url(self):
        return reverse('creator_project:funding_request_detail', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        self.object = self.get_object()
        context = super().get_context_data(**kwargs)
        context['funding_request'] = self.object
        return context
    
    def form_valid(self, form):
        self.object = self.get_object()
        
        # Submit to expert
        success = self.object.submit_to_expert()
        
        if success:
            messages.success(self.request, 'درخواست اعتبار با موفقیت برای کارشناس ارسال شد.')
        else:
            messages.error(self.request, 'خطا در ارسال درخواست. لطفا با مدیر سیستم تماس بگیرید.')
            
        return super().form_valid(form)


class ExpertReviewView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """View for experts to review funding requests"""
    model = FundingRequest
    form_class = ExpertFundingReviewForm
    template_name = 'creator_project/expert_review_form.html'
    
    def test_func(self):
        # Only experts can review and only if it's in the right state
        funding_request = self.get_object()
        user = self.request.user
        
        # Must be an expert and the request must be in the correct state
        return (
            user.is_expert and 
            funding_request.status == 'ارسال شده به کارشناس' and
            (user == funding_request.expert_user or not funding_request.expert_user)
        )
    
    def get_success_url(self):
        return reverse('creator_project:funding_request_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        action = form.cleaned_data.get('action')
        
        # Set the expert user if not already set
        if not self.object.expert_user:
            self.object.expert_user = self.request.user
        
        if action == 'approve':
            # Approve and send to chief
            self.object.expert_approve()
            self.object.send_to_chief()
            messages.success(self.request, 'درخواست اعتبار تایید و برای رئیس ارسال شد.')
        else:
            # Reject with reason
            rejection_reason = form.cleaned_data.get('expert_rejection_reason')
            self.object.expert_reject(rejection_reason)
            messages.warning(self.request, 'درخواست اعتبار رد شد و به استان برگشت خورد.')
        
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['funding_request'] = self.get_object()
        
        # Pass the suggestion reason from form to template
        if hasattr(self.get_form(), 'suggestion_reason'):
            context['suggestion_reason'] = self.get_form().suggestion_reason
            context['suggested_action'] = self.get_form().initial.get('suggested_action')
        
        return context


class ChiefReviewView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """View for chief executives to review funding requests"""
    model = FundingRequest
    form_class = ChiefFundingReviewForm
    template_name = 'creator_project/chief_review_form.html'
    
    def test_func(self):
        # Only chief executives can review and only if it's in the right state
        funding_request = self.get_object()
        user = self.request.user
        
        # Must be a chief and the request must be in the correct state
        return (
            user.is_chief_executive and 
            funding_request.status == 'ارسال شده به رئیس'
        )
    
    def get_success_url(self):
        action = self.request.POST.get('action')
        if action == 'approve':
            return reverse('creator_project:funding_table')
        return reverse('creator_project:funding_request_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        action = form.cleaned_data.get('action')
        
        # Set the chief user if not already set
        if not self.object.chief_user:
            self.object.chief_user = self.request.user
        
        if action == 'approve':
            # Approve with final amount
            final_amount = form.cleaned_data.get('final_amount')
            self.object.chief_approve(final_amount)
            messages.success(self.request, 'درخواست اعتبار تایید شد و به جدول اعتبارات اضافه شد.')
        else:
            # Reject with reason
            rejection_reason = form.cleaned_data.get('chief_rejection_reason')
            self.object.chief_reject(rejection_reason)
            messages.warning(self.request, 'درخواست اعتبار رد شد و به استان برگشت خورد.')
        
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['funding_request'] = self.get_object()
        return context


class FundingTableView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """View for the funding table (جدول اعتبارات)"""
    model = FundingRequest
    template_name = 'creator_project/funding_table.html'
    context_object_name = 'funding_requests'
    
    def test_func(self):
        # Only chief executives and admins can see the funding table
        user = self.request.user
        return user.is_chief_executive or user.is_admin
    
    def get_queryset(self):
        # Only show approved requests that are not archived
        return FundingRequest.objects.filter(
            status='تایید شده'
        ).order_by('-approved_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'جدول اعتبارات'
        
        # Calculate the total sum of final_amount
        total_amount = sum(request.final_amount or 0 for request in context['funding_requests'])
        context['total_amount'] = total_amount
        
        return context


class FundingHistoryView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """View for the funding history (تاریخچه اعتبارات)"""
    model = FundingRequest
    template_name = 'creator_project/funding_history.html'
    context_object_name = 'funding_requests'
    
    def test_func(self):
        # Only chief executives and admins can see the funding history
        user = self.request.user
        return user.is_chief_executive or user.is_admin
    
    def get_queryset(self):
        # Only show archived requests
        return FundingRequest.objects.filter(
            status='در تاریخچه'
        ).order_by('-archived_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'تاریخچه اعتبارات'
        
        # Calculate the total sum of final_amount
        total_amount = sum(request.final_amount or 0 for request in context['funding_requests'])
        context['total_amount'] = total_amount
        
        return context


class ArchiveFundingRequestsView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    """View to archive all approved funding requests"""
    template_name = 'creator_project/archive_funding_requests.html'
    form_class = forms.Form  # Empty form, just for confirmation
    success_url = reverse_lazy('creator_project:funding_table')
    
    def test_func(self):
        # Only chief executives and admins can archive funding requests
        user = self.request.user
        return user.is_chief_executive or user.is_admin
    
    def form_valid(self, form):
        # Archive all approved funding requests
        approved_requests = FundingRequest.objects.filter(status='تایید شده')
        count = approved_requests.count()
        
        for request in approved_requests:
            request.archive()
        
        messages.success(self.request, f'{count} درخواست اعتبار با موفقیت به تاریخچه اعتبارات منتقل شد.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Count how many requests will be archived
        context['archive_count'] = FundingRequest.objects.filter(status='تایید شده').count()
        return context


class ExportFundingTableView(LoginRequiredMixin, UserPassesTestMixin, View):
    """View to export the funding table as Excel"""
    
    def test_func(self):
        # Only chief executives and admins can export the funding table
        user = self.request.user
        return user.is_chief_executive or user.is_admin
    
    def get(self, request, *args, **kwargs):
        import io
        import xlsxwriter
        
        # Create an in-memory output file for the Excel workbook
        output = io.BytesIO()
        
        # Create a workbook and add a worksheet
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('جدول اعتبارات')
        
        # Add formats
        header_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': '#D7E4BC',
            'border': 1
        })
        
        cell_format = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter',
            'border': 1
        })
        
        number_format = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'num_format': '#,##0'
        })
        
        # Make the columns wider
        worksheet.set_column(0, 0, 20)  # استان
        worksheet.set_column(1, 1, 30)  # طرح
        worksheet.set_column(2, 2, 20)  # نوع طرح
        worksheet.set_column(3, 3, 30)  # نام پروژه
        worksheet.set_column(4, 4, 20)  # نوع پروژه
        worksheet.set_column(6, 5, 20)  # شهر
        worksheet.set_column(7, 7, 40)  # آدرس
        worksheet.set_column(8, 8, 15)  # عرصه
        worksheet.set_column(9, 9, 15)  # اعیان
        worksheet.set_column(10, 10, 15)  # طبقه
        worksheet.set_column(11, 11, 20)  # پیشرفت فیزیکی
        worksheet.set_column(12, 12, 20)  # وضعیت مجوز
        worksheet.set_column(13, 13, 20)  # کد مجوز
        worksheet.set_column(14, 14, 20)  # مجموع دیون
        worksheet.set_column(15, 15, 30)  # اعتبار مورد نیاز تکمیل قرار داد ها
        worksheet.set_column(16, 16, 30)  # اعتبار مورد نیاز تکمیل پروژه
        worksheet.set_column(17, 17, 15)  # اولویت
        worksheet.set_column(18, 18, 20)  # مبلغ نهایی
        worksheet.set_column(19, 19, 40)  # توضیحات استان
        
        # Set RTL (right-to-left) mode for the worksheet
        worksheet.right_to_left()
        
        # Write the header row
        headers = [
            'استان',
            'طرح',
            'نوع طرح',
            'نام پروژه',
            'نوع پروژه',
            'شهر',
            'آدرس',
            'عرصه',
            'اعیان',
            'طبقه',
            'پیشرفت فیزیکی',
            'وضعیت مجوز',
            'کد مجوز',
            'مجموع دیون',
            'اعتبار مورد نیاز تکمیل قرار داد ها',
            'اعتبار مورد نیاز تکمیل پروژه',
            'اولویت',
            'مبلغ نهایی',
            'توضیحات استان'
        ]
        
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
        
        # Get all approved funding requests
        approved_requests = FundingRequest.objects.filter(status='تایید شده')
        
        # Write data rows
        for row, request in enumerate(approved_requests, start=1):
            project = request.project
            
            # Write project data according to new order
            worksheet.write(row, 0, project.province, cell_format)  # استان
            program_name = project.program.title if project.program else ''
            worksheet.write(row, 1, program_name, cell_format)  # طرح
            program_type = project.program.program_type if project.program else ''
            worksheet.write(row, 2, program_type, cell_format)  # نوع طرح
            worksheet.write(row, 3, project.name, cell_format)  # نام پروژه
            worksheet.write(row, 4, project.city, cell_format)  # شهر
            worksheet.write(row, 5, project.project_type, cell_format)  # نوع پروژه
            worksheet.write(row, 6, project.city, cell_format)  # شهر (duplicate as requested)
            # Get address from program
            address = project.program.address if project.program else ''
            worksheet.write(row, 7, address, cell_format)  # آدرس
            worksheet.write(row, 8, project.area_size or 0, number_format)  # عرصه
            worksheet.write(row, 9, project.notables or 0, number_format)  # اعیان
            worksheet.write(row, 10, project.floor or 0, number_format)  # طبقه
            worksheet.write(row, 11, project.physical_progress or 0, number_format)  # پیشرفت فیزیکی
            license_state = project.program.license_state if project.program else ''
            worksheet.write(row, 12, license_state, cell_format)  # وضعیت مجوز
            license_code = project.program.license_code if project.program else ''
            worksheet.write(row, 13, license_code, cell_format)  # کد مجوز
            worksheet.write(row, 14, project.cached_total_debt or 0, number_format)  # مجموع دیون
            worksheet.write(row, 15, project.cached_required_credit_contracts or 0, number_format)  # اعتبار مورد نیاز تکمیل قرار داد ها
            worksheet.write(row, 16, project.cached_required_credit_project or 0, number_format)  # اعتبار مورد نیاز تکمیل پروژه
            worksheet.write(row, 17, request.priority, cell_format)  # اولویت
            worksheet.write(row, 18, request.final_amount or 0, number_format)  # مبلغ نهایی
            worksheet.write(row, 19, request.province_description, cell_format)  # توضیحات استان
        
        # Close the workbook
        workbook.close()
        
        # Seek to the beginning of the stream
        output.seek(0)
        
        # Create the HttpResponse with Excel content type
        filename = f"funding_table_{datetime.now().strftime('%Y-%m-%d')}.xlsx"
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename={filename}'
        
        return response


class ProvinceFundingRequestView(LoginRequiredMixin, TemplateView):
    template_name = 'creator_project/province_funding_request.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        provinces = user.get_assigned_provinces()
        
        # If no assigned provinces found via UserProvince, fall back to direct province field
        if not provinces and user.province:
            provinces = [user.province]
        
        # Show all projects in user's provinces (not just approved ones)
        if provinces:
            projects = Project.objects.filter(
                models.Q(province__in=provinces) | 
                models.Q(created_by=user)
            )
            print(f"DEBUG: Found {projects.count()} projects for provinces {provinces}")
            # Log each project for debugging
            for project in projects:
                print(f"DEBUG: Project {project.id}: {project.name} - Province: {project.province} - Approved: {project.is_approved}")
        else:
            projects = Project.objects.none()
            print("DEBUG: No provinces found for user, showing no projects")
            
        context['projects'] = projects
        return context

@login_required
def allocation_list(request, project_id):
    """View for listing all allocations of a project with edit/delete options"""
    project = get_object_or_404(Project, id=project_id)
    
    # Check permissions
    if not (request.user.is_admin or request.user.is_ceo or request.user.is_expert or 
            request.user.is_chief_executive or project.created_by == request.user):
        messages.error(request, 'شما اجازه دسترسی به این صفحه را ندارید.')
        return redirect('creator_project:project_detail', project_id=project.id)
    
    allocations = project.allocations.all().order_by('-allocation_date')
    
    context = {
        'project': project,
        'allocations': allocations,
    }
    return render(request, 'creator_project/allocation_list.html', context)


@login_required
def allocation_edit(request, allocation_id):
    """View for editing an allocation"""
    allocation = get_object_or_404(ProjectFinancialAllocation, id=allocation_id)
    project = allocation.project
    
    # Check permissions
    if not (request.user.is_admin or request.user.is_ceo or request.user.is_expert or 
            request.user.is_chief_executive or project.created_by == request.user):
        messages.error(request, 'شما اجازه ویرایش این تخصیص را ندارید.')
        return redirect('creator_project:allocation_list', project_id=project.id)
    
    if request.method == 'POST':
        # ProjectFinancialAllocationForm not implemented yet
        form = forms.Form(request.POST, instance=allocation)
        if form.is_valid():
            form.save()
            messages.success(request, 'تخصیص مالی با موفقیت بروزرسانی شد.')
            return redirect('creator_project:allocation_list', project_id=project.id)
    else:
        # ProjectFinancialAllocationForm not implemented yet
        form = forms.Form(instance=allocation)
    
    context = {
        'form': form,
        'project': project,
        'allocation': allocation,
    }
    return render(request, 'creator_project/allocation_form.html', context)


@login_required
def allocation_delete(request, allocation_id):
    """View for deleting an allocation"""
    allocation = get_object_or_404(ProjectFinancialAllocation, id=allocation_id)
    project = allocation.project
    
    # Check permissions
    if not (request.user.is_admin or request.user.is_ceo or request.user.is_expert or 
            request.user.is_chief_executive or project.created_by == request.user):
        messages.error(request, 'شما اجازه حذف این تخصیص را ندارید.')
        return redirect('creator_project:allocation_list', project_id=project.id)
    
    if request.method == 'POST':
        allocation.delete()
        messages.success(request, 'تخصیص مالی با موفقیت حذف شد.')
        return redirect('creator_project:allocation_list', project_id=project.id)
    
    context = {
        'allocation': allocation,
        'project': project,
    }
    return render(request, 'creator_project/allocation_confirm_delete.html', context)

@login_required
def subproject_list(request, project_id):
    """View for listing all subprojects of a project with delete options"""
    project = get_object_or_404(Project, id=project_id)
    
    # Check permissions
    if not (request.user.is_admin or request.user.is_ceo or request.user.is_expert or 
            request.user.is_chief_executive or project.created_by == request.user):
        messages.error(request, 'شما اجازه دسترسی به این صفحه را ندارید.')
        return redirect('creator_project:project_detail', project_id=project.id)
    
    subprojects = project.subprojects.all().order_by('sub_project_number')
    
    context = {
        'project': project,
        'subprojects': subprojects,
    }
    return render(request, 'creator_project/subproject_list.html', context)


@login_required
def subproject_delete(request, subproject_id):
    """View for deleting a subproject"""
    from creator_subproject.models import SubProject
    
    subproject = get_object_or_404(SubProject, id=subproject_id)
    project = subproject.project
    
    # Check permissions
    if not (request.user.is_admin or project.created_by == request.user):
        messages.error(request, 'شما اجازه حذف این زیرپروژه را ندارید.')
        return redirect('creator_project:subproject_list', project_id=project.id)
    
    # Check if subproject can be deleted (no related documents/payments)
    if subproject.allocations.exists() or subproject.payments.exists():
        messages.error(request, 'این زیرپروژه دارای اسناد مالی یا پرداختی است و قابل حذف نیست.')
        return redirect('creator_project:subproject_list', project_id=project.id)
    
    # Check if other subprojects are related to this one
    related_subprojects = SubProject.objects.filter(related_subproject=subproject)
    if related_subprojects.exists():
        related_names = [f"{sp.sub_project_type} #{sp.sub_project_number}" for sp in related_subprojects]
        messages.error(request, f'این زیرپروژه به زیرپروژه‌های دیگر مرتبط است و قابل حذف نیست. زیرپروژه‌های مرتبط: {", ".join(related_names)}')
        return redirect('creator_project:subproject_list', project_id=project.id)
    
    # Check if this subproject has gallery images
    gallery_images_count = subproject.gallery_images.count() if hasattr(subproject, 'gallery_images') else 0
    
    # Check if this subproject has update history
    update_history_count = subproject.update_history.count() if hasattr(subproject, 'update_history') else 0
    
    if request.method == 'POST':
        # Require double confirmation
        confirmation_text = request.POST.get('confirmation_text', '').strip()
        expected_confirmation = f"{subproject.sub_project_type} #{subproject.sub_project_number}"
        
        if confirmation_text != expected_confirmation:
            messages.error(request, f'تایید نادرست. لطفاً "{expected_confirmation}" را وارد کنید.')
            return redirect('creator_project:subproject_delete', subproject_id=subproject.id)
        
        subproject_name = str(subproject)
        subproject.delete()
        messages.success(request, f'زیرپروژه "{subproject_name}" با موفقیت حذف شد.')
        return redirect('creator_project:subproject_list', project_id=project.id)
    
    context = {
        'subproject': subproject,
        'project': project,
        'related_subprojects': related_subprojects,
        'gallery_images_count': gallery_images_count,
        'update_history_count': update_history_count,
        'expected_confirmation': f"{subproject.sub_project_type} #{subproject.sub_project_number}",
    }
    return render(request, 'creator_project/subproject_delete_confirm.html', context) 