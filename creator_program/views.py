from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from .models import Program
from .forms import ProgramForm
import logging

logger = logging.getLogger(__name__)


class ProgramListView(LoginRequiredMixin, ListView):
    model = Program
    template_name = 'creator_program/program_list.html'
    context_object_name = 'programs'
    
    def get_queryset(self):
        user = self.request.user
        
        # If user is admin, CEO, or chief executive, show all programs
        if user.is_admin or user.is_ceo or user.is_chief_executive:
            return Program.objects.all().order_by('-created_at')
        
        # Get user's assigned provinces
        user_provinces = user.get_assigned_provinces()
        
        # Filter programs by user's assigned provinces
        if user_provinces:
            return Program.objects.filter(province__in=user_provinces).order_by('-created_at')
        
        # If user has no province assignments, show only their own programs
        return Program.objects.filter(created_by=user).order_by('-created_at')


class ProgramDetailView(LoginRequiredMixin, DetailView):
    model = Program
    template_name = 'creator_program/program_detail.html'
    context_object_name = 'program'
    
    def get_object(self, queryset=None):
        program = super().get_object(queryset)
        user = self.request.user
        
        # Check if user has access to this program
        if not self.user_has_access(program, user):
            raise PermissionDenied("شما دسترسی به این طرح ندارید.")
        
        return program
    
    def user_has_access(self, program, user):
        """Check if user has access to the program based on province and role"""
        # Admin, CEO, and chief executive have access to all programs
        if user.is_admin or user.is_ceo or user.is_chief_executive:
            return True
        
        # Check if user has access to the program's province
        user_provinces = user.get_assigned_provinces()
        return program.province in user_provinces


class ProgramCreateView(LoginRequiredMixin, CreateView):
    model = Program
    form_class = ProgramForm
    template_name = 'creator_program/program_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Pass the user to the form
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        logger.info(f"DEBUG: Form is valid for user {self.request.user.username}")
        logger.info(f"DEBUG: Form data: {self.request.POST}")
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, "طرح با موفقیت ایجاد شد.")
        return response
    
    def form_invalid(self, form):
        logger.error(f"DEBUG: Form is invalid for user {self.request.user.username}")
        logger.error(f"DEBUG: Form errors: {form.errors}")
        logger.error(f"DEBUG: Form data: {self.request.POST}")
        # Provide a user-facing message and re-render the form so the user can correct errors
        messages.error(self.request, "لطفاً خطاهای فرم را اصلاح کنید و دوباره تلاش کنید.")
        return self.render_to_response(self.get_context_data(form=form))

    def post(self, request, *args, **kwargs):
        # Clean POST data to avoid client-side artifacts blocking server-side validation
        post_data = request.POST.copy()

        # Remove computed or readonly fields that shouldn't be validated server-side
        if 'program_opening_date' in post_data:
            post_data.pop('program_opening_date')

        # If user is a province manager, ensure province is set to one of their assigned provinces
        user = request.user
        try:
            assigned = user.get_assigned_provinces()
        except Exception:
            assigned = None

        if getattr(user, 'is_province_manager', False) and assigned:
            # Use the first assigned province as the submitted value
            post_data['province'] = assigned[0]

        # Instantiate the form with cleaned data and the user context
        form = self.get_form_class()(post_data, user=user)

        if form.is_valid():
            try:
                obj = form.save(commit=False)
                obj.created_by = user
                obj.save()
                messages.success(request, "طرح با موفقیت ایجاد شد.")
                return redirect('creator_program:program_detail', pk=obj.pk)
            except Exception as e:
                logger.exception("Error saving Program")
                messages.error(request, f"خطا در ایجاد طرح: {e}")
                return self.render_to_response(self.get_context_data(form=form))
        else:
            logger.error(f"Form invalid on POST: {form.errors}")
            messages.error(request, "لطفاً خطاهای فرم را اصلاح کنید و دوباره تلاش کنید.")
            return self.render_to_response(self.get_context_data(form=form))
    
    def get_success_url(self):
        return reverse_lazy('creator_program:program_detail', kwargs={'pk': self.object.pk})


class ProgramUpdateView(LoginRequiredMixin, UpdateView):
    model = Program
    form_class = ProgramForm
    template_name = 'creator_program/program_form.html'
    context_object_name = 'program'
    
    def get_object(self, queryset=None):
        program = super().get_object(queryset)
        user = self.request.user
        
        # Check if user has access to modify this program
        if not self.user_can_modify(program, user):
            raise PermissionDenied("شما مجوز ویرایش این طرح را ندارید.")
        
        return program
    
    def user_can_modify(self, program, user):
        """Check if user can modify the program based on province and role"""
        # Admin, CEO, and chief executive can modify all programs
        if user.is_admin or user.is_ceo or user.is_chief_executive:
            return True
        
        # Check if user has access to the program's province
        user_provinces = user.get_assigned_provinces()
        return program.province in user_provinces
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Pass the user to the form
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        # Set _update_user for tracking changes
        form.instance._update_user = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, "طرح با موفقیت به‌روزرسانی شد.")
        return response

    def post(self, request, *args, **kwargs):
        # Pre-process POST data similarly to create view to avoid stuck processing
        self.object = self.get_object()
        post_data = request.POST.copy()

        if 'program_opening_date' in post_data:
            post_data.pop('program_opening_date')

        user = request.user
        try:
            assigned = user.get_assigned_provinces()
        except Exception:
            assigned = None

        if getattr(user, 'is_province_manager', False) and assigned:
            post_data['province'] = assigned[0]

        form = self.get_form_class()(post_data, instance=self.object, user=user)

        if form.is_valid():
            try:
                form.instance._update_user = user
                form.save()
                messages.success(request, "طرح با موفقیت به‌روزرسانی شد.")
                return redirect('creator_program:program_detail', pk=self.object.pk)
            except Exception as e:
                logger.exception("Error updating Program")
                messages.error(request, f"خطا در به‌روزرسانی طرح: {e}")
                return self.render_to_response(self.get_context_data(form=form))
        else:
            logger.error(f"Program update form invalid: {form.errors}")
            messages.error(request, "لطفاً خطاهای فرم را اصلاح کنید و دوباره تلاش کنید.")
            return self.render_to_response(self.get_context_data(form=form))
    
    def get_success_url(self):
        return reverse_lazy('creator_program:program_detail', kwargs={'pk': self.object.pk})