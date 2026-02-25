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
        return super().form_invalid(form)
    
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
    
    def get_success_url(self):
        return reverse_lazy('creator_program:program_detail', kwargs={'pk': self.object.pk})