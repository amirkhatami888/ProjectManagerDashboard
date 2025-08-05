from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponseForbidden

from creator_project.models import Project
from creator_subproject.models import SubProject
from .models import ProjectReview, SubProjectReview
from .forms import ProjectReviewForm, SubProjectReviewForm

@login_required
def review_project(request, project_id):
    """View for reviewing a project - now redirects to combined interface"""
    messages.info(request, 'بررسی پروژه‌ها اکنون از طریق بخش گزارش گیر و جستجو انجام می‌شود.')
    return redirect('search_history')

@login_required
def review_subproject(request, pk):
    """Review a subproject and add comments"""
    subproject = get_object_or_404(SubProject, pk=pk)
    
    # Check if user is authorized
    if not (request.user.is_admin or request.user.is_expert or request.user.is_vice_chief_executive):
        messages.error(request, 'شما مجاز به انجام این عملیات نیستید.')
        return redirect('creator_subproject:subproject_detail', pk=pk)
    
    # Check if the parent project is submitted but not approved
    if not (subproject.project.is_submitted and not subproject.project.is_approved):
        messages.error(request, 'این زیرپروژه قابل بررسی نیست. پروژه مربوطه باید در وضعیت "در انتظار بررسی" باشد.')
        return redirect('creator_subproject:subproject_detail', pk=pk)
    
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            # Add review comment
            review = Review.objects.create(
                subproject=subproject,
                reviewer=request.user,
                field_name=form.cleaned_data['field_name'],
                comment=form.cleaned_data['comment'],
                recommendation=form.cleaned_data['recommendation']
            )
            
            # If recommendation is to approve, update project status
            if form.cleaned_data['recommendation'] == 'approve':
                project = subproject.project
                project.is_approved = True
                project.save(update_fields=['is_approved'])
                
                # Clear rejection comments when project is approved
                from creator_project.models import ProjectRejectionComment
                ProjectRejectionComment.objects.filter(project=project).delete()
            
            # If recommendation is to reject, update project status
            elif form.cleaned_data['recommendation'] == 'reject':
                project = subproject.project
                project.is_submitted = False
                project.save(update_fields=['is_submitted'])
            
            messages.success(request, 'بررسی شما با موفقیت ثبت شد.')
            return redirect('creator_subproject:subproject_detail', pk=pk)
    else:
        form = ReviewForm()
    
    return render(request, 'creator_review/review_form.html', {
        'form': form,
        'subproject': subproject
    })

@login_required
def review_project(request, project_id):
    """View for experts to review a project"""
    # Check if user is an expert
    if not request.user.is_expert:
        messages.error(request, 'شما مجوز دسترسی به این صفحه را ندارید.')
        return redirect('home')
    
    project = get_object_or_404(Project, id=project_id)
    
    # Check if project needs review
    if not (project.is_submitted and not project.is_approved):
        messages.error(request, 'این پروژه در وضعیت نیازمند بررسی نیست.')
        return redirect('creator_project:project_detail', pk=project_id)
    
    # Check if this expert has already reviewed this project
    existing_review = ProjectReview.objects.filter(project=project, reviewer=request.user).first()
    
    if request.method == 'POST':
        form = ProjectReviewForm(request.POST, instance=existing_review)
        if form.is_valid():
            review = form.save(commit=False)
            review.project = project
            review.reviewer = request.user
            review.save()
            
            # Update project status based on approval
            if review.is_approved:
                project.is_approved = True
                
                # Clear rejection comments when project is approved
                from creator_project.models import ProjectRejectionComment
                ProjectRejectionComment.objects.filter(project=project).delete()
                
                messages.success(request, 'پروژه با موفقیت تأیید شد.')
            else:
                messages.info(request, 'پروژه رد شد و نیاز به اصلاحات دارد.')
            project.save()
            
            return redirect('expert_dashboard')
    else:
        form = ProjectReviewForm(instance=existing_review)
    
    context = {
        'project': project,
        'form': form,
        'existing_review': existing_review
    }
    
    return render(request, 'creator_review/review_project.html', context)

@login_required
def review_subproject(request, subproject_id):
    """View for experts to review a subproject"""
    # Check if user is an expert
    if not request.user.is_expert:
        messages.error(request, 'شما مجوز دسترسی به این صفحه را ندارید.')
        return redirect('home')
    
    subproject = get_object_or_404(SubProject, id=subproject_id)
    
    # Check if subproject needs review
    if not (subproject.is_submitted and not subproject.is_approved):
        messages.error(request, 'این زیرپروژه در وضعیت نیازمند بررسی نیست.')
        return redirect('subproject_detail', subproject_id=subproject_id)
    
    # Check if this expert has already reviewed this subproject
    existing_review = SubProjectReview.objects.filter(subproject=subproject, reviewer=request.user).first()
    
    if request.method == 'POST':
        form = SubProjectReviewForm(request.POST, instance=existing_review)
        if form.is_valid():
            review = form.save(commit=False)
            review.subproject = subproject
            review.reviewer = request.user
            review.save()
            
            # Update subproject status based on approval
            if review.is_approved:
                subproject.is_approved = True
                messages.success(request, 'زیرپروژه با موفقیت تأیید شد.')
            else:
                messages.info(request, 'زیرپروژه رد شد و نیاز به اصلاحات دارد.')
            subproject.save()
            
            return redirect('expert_dashboard')
    else:
        form = SubProjectReviewForm(instance=existing_review)
    
    context = {
        'subproject': subproject,
        'form': form,
        'existing_review': existing_review
    }
    
    return render(request, 'creator_review/review_subproject.html', context)
