from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from .models import Project, ALL_Project, ProjectRejectionComment, ProjectFinancialAllocation
from .forms import ProjectForm, ProjectRejectionForm, ProjectFinancialAllocationForm
import jdatetime
from datetime import datetime

@login_required
def project_list(request):
    # If user is admin, CEO, or chief executive, show all projects
    if request.user.is_admin or request.user.is_ceo or request.user.is_chief_executive:
        projects = Project.objects.all()
    # If user is expert or vice chief executive, show submitted projects
    elif request.user.is_expert or request.user.is_vice_chief_executive:
        projects = Project.objects.filter(is_submitted=True)
    # If user is province manager, show projects from their assigned provinces
    elif request.user.is_province_manager:
        # Get user's assigned provinces
        user_provinces = request.user.get_assigned_provinces()
        if user_provinces:
            # Show all projects from user's assigned provinces
            projects = Project.objects.filter(province__in=user_provinces)
        else:
            # Fallback to user's own projects if no province assignments
            projects = Project.objects.filter(created_by=request.user)
    else:
        return HttpResponseForbidden("You don't have permission to view projects.")
    
    return render(request, 'creator_project/project_list.html', {
        'projects': projects,
        'debug': True
    })

@login_required
def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    
    # Check permissions
    if not (request.user.is_admin or request.user.is_ceo or request.user.is_chief_executive or 
            request.user.is_vice_chief_executive or request.user.is_expert or 
            (request.user.is_province_manager and (
                project.created_by == request.user or 
                project.province in request.user.get_assigned_provinces()
            ))):
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
    
    print(f"DEBUG: User attempting to create project: {request.user.username}")
    print(f"DEBUG: User role: {request.user.role}")
    print(f"DEBUG: User province: {request.user.province}")
    print(f"DEBUG: Is province manager: {request.user.is_province_manager}")
    
    if request.method == 'POST':
        # Clean up the form data to avoid validation issues
        post_data = request.POST.copy()
        
        # Always remove the estimated_opening_time field - we'll handle it separately
        if 'estimated_opening_time' in post_data:
            post_data.pop('estimated_opening_time')
            print("DEBUG: Removed estimated_opening_time field from form validation")
        
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
                project.credit_required = 0
                project.credit_required_technical = 0
            
                # Ensure province is set to the user's province if they are a province manager
                if request.user.is_province_manager and request.user.province:
                    project.province = request.user.province
                    print(f"DEBUG: Setting project province to {project.province}")
                
                # Handle Persian date for estimated_opening_time
                persian_date = request.POST.get('estimated_opening_time')
                if persian_date and persian_date.strip():
                    try:
                        # Parse Persian date (format: YYYY/MM/DD)
                        parts = persian_date.split('/')
                        if len(parts) == 3:
                            j_date = jdatetime.date(int(parts[0]), int(parts[1]), int(parts[2]))
                            g_date = j_date.togregorian()
                            project.estimated_opening_time = g_date
                            print(f"DEBUG: Converted date {persian_date} to {g_date}")
                    except Exception as e:
                        print(f"DEBUG: Error converting date: {str(e)}")
                        # Don't fail - just leave the date as None
                        project.estimated_opening_time = None
                else:
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
    else:
        form = ProjectForm(user=request.user)
    
    return render(request, 'creator_project/project_form.html', {
        'form': form, 
        'is_create': True,
        'debug': True
    })

@login_required
def project_update(request, pk):
    project = get_object_or_404(Project, pk=pk)
    
    # Check if user has permission to update this project
    if request.user.is_admin:
        # Admins can update any project
        pass
    elif request.user.is_province_manager:
        # Province managers can update projects from their assigned provinces
        user_provinces = request.user.get_assigned_provinces()
        if user_provinces and project.province in user_provinces:
            # User can update projects from their assigned provinces
            pass
        elif project.created_by == request.user:
            # User can update their own projects (fallback)
            pass
        else:
            return HttpResponseForbidden("You don't have permission to update this project.")
    else:
        return HttpResponseForbidden("You don't have permission to update this project.")
    
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project, user=request.user)
        if form.is_valid():
            # Set the current user as the updater to track in history
            project._update_user = request.user
            
            # Ensure province managers can't change the province
            if request.user.is_province_manager and request.user.province:
                form.instance.province = request.user.province
                
            # Handle Persian date for estimated_opening_time
            if request.POST.get('estimated_opening_time'):
                try:
                    # Convert Persian date to Gregorian
                    persian_date = request.POST.get('estimated_opening_time')
                    if persian_date:
                        # Parse Persian date (format: YYYY/MM/DD)
                        parts = persian_date.split('/')
                        if len(parts) == 3:
                            j_date = jdatetime.date(int(parts[0]), int(parts[1]), int(parts[2]))
                            g_date = j_date.togregorian()
                            form.instance.estimated_opening_time = g_date
                except Exception as e:
                    # Log the error and continue (optional)
                    print(f"Error converting date: {e}")
                
            form.save()
            messages.success(request, "پروژه با موفقیت به‌روزرسانی شد.")
            return redirect('creator_project:project_detail', pk=project.pk)
    else:
        form = ProjectForm(instance=project, user=request.user)
    
    return render(request, 'creator_project/project_form.html', {'form': form, 'project': project, 'is_create': False})

@login_required
def project_delete(request, pk):
    project = get_object_or_404(Project, pk=pk)
    
    # Only admins, the project creator, or province managers from the same province can delete projects
    if not (request.user.is_admin or 
            project.created_by == request.user or
            (request.user.is_province_manager and project.province in request.user.get_assigned_provinces())):
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
    
    # Only admin, expert, or vice chief executive can approve projects
    if not (request.user.is_admin or request.user.is_expert or request.user.is_vice_chief_executive):
        return HttpResponseForbidden("You don't have permission to approve projects.")
    
    # Update project status
    project.is_approved = True
    # Set the current user as the updater to track in history
    project._update_user = request.user
    project.save()
    
    messages.success(request, "پروژه با موفقیت تایید شد.")
    return redirect('creator_project:project_detail', pk=project.pk)

@login_required
def project_reject(request, pk):
    project = get_object_or_404(Project, pk=pk)
    
    # Only admin, expert, or vice chief executive can reject projects
    if not (request.user.is_admin or request.user.is_expert or request.user.is_vice_chief_executive):
        return HttpResponseForbidden("You don't have permission to reject projects.")
    
    if request.method == 'POST':
        form = ProjectRejectionForm(request.POST)
        if form.is_valid():
            # Create rejection comment
            ProjectRejectionComment.objects.create(
                project=project,
                expert=request.user,
                field_name=form.cleaned_data['field_name'],
                comment=form.cleaned_data['comment']
            )
            
            # Update project status
            project.is_submitted = False
            # Set the current user as the updater to track in history
            project._update_user = request.user
            project.save()
            
            messages.success(request, "پروژه با موفقیت رد شد.")
            return redirect('creator_project:project_detail', pk=project.pk)
    else:
        form = ProjectRejectionForm()
    
    return render(request, 'creator_project/project_reject_form.html', {'form': form, 'project': project})

@login_required
def project_financials(request, pk):
    project = get_object_or_404(Project, pk=pk)
    
    # Check permissions
    if not (request.user.is_admin or request.user.is_expert or 
            (request.user.is_province_manager and (
                project.created_by == request.user or 
                project.province in request.user.get_assigned_provinces()
            ))):
        return HttpResponseForbidden("You don't have permission to view project financials.")
    
    # Fetch all financial data
    # This is a placeholder for actual implementation
    return render(request, 'creator_project/project_financials.html', {'project': project})

@login_required
def project_add_allocation(request, pk):
    project = get_object_or_404(Project, pk=pk)
    
    # Check permissions
    if not (request.user.is_admin or request.user.is_expert or 
            (request.user.is_province_manager and (
                project.created_by == request.user or 
                project.province in request.user.get_assigned_provinces()
            ))):
        return HttpResponseForbidden("You don't have permission to add allocations.")
    
    if request.method == 'POST':
        form = ProjectFinancialAllocationForm(request.POST)
        if form.is_valid():
            allocation = form.save(commit=False)
            allocation.project = project
            
            # Handle Persian date for allocation_date
            persian_date = request.POST.get('allocation_date')
            if persian_date:
                try:
                    # Parse Persian date (format: YYYY/MM/DD)
                    parts = persian_date.split('/')
                    if len(parts) == 3:
                        j_date = jdatetime.date(int(parts[0]), int(parts[1]), int(parts[2]))
                        g_date = j_date.togregorian()
                        allocation.allocation_date = g_date
                except Exception as e:
                    # Log the error and use the default (today)
                    print(f"Error converting date: {e}")
            
            allocation.save()
            messages.success(request, "تخصیص مالی با موفقیت اضافه شد.")
            return redirect('creator_project:project_detail', pk=project.pk)
    else:
        form = ProjectFinancialAllocationForm()
    
    return render(request, 'creator_project/allocation_form.html', {'form': form, 'project': project}) 