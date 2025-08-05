from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from .models import Program
from .forms import ProgramForm


class ProgramListView(LoginRequiredMixin, ListView):
    model = Program
    template_name = 'creator_program/program_list.html'
    context_object_name = 'programs'
    
    def get_queryset(self):
        # Filter programs based on user role if needed
        return Program.objects.all().order_by('-created_at')


class ProgramDetailView(LoginRequiredMixin, DetailView):
    model = Program
    template_name = 'creator_program/program_detail.html'
    context_object_name = 'program'


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
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, "طرح با موفقیت ایجاد شد.")
        return response
    
    def get_success_url(self):
        return reverse_lazy('creator_program:program_detail', kwargs={'pk': self.object.pk})


class ProgramUpdateView(LoginRequiredMixin, UpdateView):
    model = Program
    form_class = ProgramForm
    template_name = 'creator_program/program_form.html'
    context_object_name = 'program'
    
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