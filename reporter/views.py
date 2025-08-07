from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q, Avg, Count, Case, When, IntegerField, F
from django.db.models.functions import Coalesce
from django.utils import timezone
from datetime import datetime, timedelta
from django.http import JsonResponse, HttpResponse
from decimal import Decimal
import csv
import xlsxwriter
from io import BytesIO
import json

from creator_project.models import Project, ProjectUpdateHistory
from creator_subproject.models import SubProject, SubProjectUpdateHistory
from creator_subproject.views import parse_jalali_date
from creator_review.models import ProjectReview, SubProjectReview
from creator_program.models import Program
from .models import ProjectReport, SubProjectReport, GeneratedReport, SearchHistory, ProjectFinancialAllocation
from .forms import ProjectReportForm, SubProjectReportForm

@login_required
def reporter_dashboard(request):
    """Dashboard view for reports"""
    # Check if the user is a province manager or expert - restrict access
    if request.user.is_province_manager or request.user.is_expert:
        messages.error(request, "شما مجوز دسترسی به بخش گزارش‌گیری را ندارید.")
        return redirect('dashboard:dashboard')
        
    user = request.user
    project_reports = ProjectReport.objects.filter(created_by=user)
    subproject_reports = SubProjectReport.objects.filter(created_by=user)
    
    context = {
        'project_reports': project_reports,
        'subproject_reports': subproject_reports,
        'total_reports': project_reports.count() + subproject_reports.count()
    }
    return render(request, 'reporter/dashboard.html', context)

class ProjectReportListView(LoginRequiredMixin, ListView):
    model = ProjectReport
    template_name = 'reporter/project_report_list.html'
    context_object_name = 'reports'
    paginate_by = 10
    
    def get_queryset(self):
        return ProjectReport.objects.filter(created_by=self.request.user)

class ProjectReportDetailView(LoginRequiredMixin, DetailView):
    model = ProjectReport
    template_name = 'reporter/project_report_detail.html'
    context_object_name = 'report'

class ProjectReportCreateView(LoginRequiredMixin, CreateView):
    model = ProjectReport
    form_class = ProjectReportForm
    template_name = 'reporter/project_report_form.html'
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, "Project report created successfully.")
        return super().form_valid(form)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_success_url(self):
        return reverse('project_report_detail', kwargs={'pk': self.object.pk})

class ProjectReportUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = ProjectReport
    form_class = ProjectReportForm
    template_name = 'reporter/project_report_form.html'
    
    def test_func(self):
        report = self.get_object()
        return self.request.user == report.created_by
    
    def form_valid(self, form):
        messages.success(self.request, "Report updated successfully.")
        return super().form_valid(form)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_success_url(self):
        return reverse('project_report_detail', kwargs={'pk': self.object.pk})

class ProjectReportDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = ProjectReport
    template_name = 'reporter/project_report_confirm_delete.html'
    
    def test_func(self):
        report = self.get_object()
        return self.request.user == report.created_by
    
    def get_success_url(self):
        messages.success(self.request, "Report deleted successfully.")
        return reverse('project_report_list')

# SubProject Report Views
class SubProjectReportListView(LoginRequiredMixin, ListView):
    model = SubProjectReport
    template_name = 'reporter/subproject_report_list.html'
    context_object_name = 'reports'
    paginate_by = 10
    
    def get_queryset(self):
        return SubProjectReport.objects.filter(created_by=self.request.user)

class SubProjectReportDetailView(LoginRequiredMixin, DetailView):
    model = SubProjectReport
    template_name = 'reporter/subproject_report_detail.html'
    context_object_name = 'report'

class SubProjectReportCreateView(LoginRequiredMixin, CreateView):
    model = SubProjectReport
    form_class = SubProjectReportForm
    template_name = 'reporter/subproject_report_form.html'
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, "Report created successfully.")
        return super().form_valid(form)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_success_url(self):
        return reverse('subproject_report_detail', kwargs={'pk': self.object.pk})

class SubProjectReportUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = SubProjectReport
    form_class = SubProjectReportForm
    template_name = 'reporter/subproject_report_form.html'
    
    def test_func(self):
        report = self.get_object()
        return self.request.user == report.created_by
    
    def form_valid(self, form):
        messages.success(self.request, "Report updated successfully.")
        return super().form_valid(form)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_success_url(self):
        return reverse('subproject_report_detail', kwargs={'pk': self.object.pk})

class SubProjectReportDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = SubProjectReport
    template_name = 'reporter/subproject_report_confirm_delete.html'
    
    def test_func(self):
        report = self.get_object()
        return self.request.user == report.created_by
    
    def get_success_url(self):
        messages.success(self.request, "Report deleted successfully.")
        return reverse('subproject_report_list')

@login_required
def create_report_from_search(request):
    """Create a new report based on search results"""
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('search_history')
    
    # Get search parameters from form
    query = request.POST.get('query', '')
    from_date = request.POST.get('from_date', '')
    to_date = request.POST.get('to_date', '')
    type_filter = request.POST.get('type_filter', 'all')
    field_filter = request.POST.get('field_filter', '')
    
    # Get report details
    report_title = request.POST.get('report_title', '')
    report_type = request.POST.get('report_type', 'summary')
    report_content = request.POST.get('report_content', '')
    
    if not report_title or not report_content:
        messages.error(request, 'Please enter report title and content.')
        return redirect('search_history')
    
    # Generate content supplement based on search parameters
    search_criteria = []
    if query:
        search_criteria.append(f"Search query: {query}")
    if from_date:
        search_criteria.append(f"From date: {from_date}")
    if to_date:
        search_criteria.append(f"To date: {to_date}")
    if type_filter != 'all':
        search_criteria.append(f"Type: {'Project' if type_filter == 'project' else 'Subproject'}")
    if field_filter:
        search_criteria.append(f"Field: {field_filter}")
    
    search_summary = "Search with the following criteria:\n- " + "\n- ".join(search_criteria) if search_criteria else ""
    
    # Get actual result counts from the session if available
    total_project_results = request.session.get('total_project_results', 0)
    total_subproject_results = request.session.get('total_subproject_results', 0)
    
    result_summary = f"\n\nSearch results: {total_project_results} projects and {total_subproject_results} subprojects"
    
    # Combine user content with search parameters
    full_content = f"{report_content}\n\n---\n{search_summary}{result_summary}"

    # Create appropriate report based on type_filter
    created_report = None
    
    try:
        from_date_obj = datetime.strptime(from_date, '%Y-%m-%d').date() if from_date else None
        to_date_obj = datetime.strptime(to_date, '%Y-%m-%d').date() if to_date else None
    except ValueError:
        from_date_obj = None
        to_date_obj = None
        
    if type_filter == 'project':
        # Try to get the first project from the results to associate with this report
        try:
            project_id = request.session.get('first_project_id')
            if project_id:
                project = Project.objects.get(id=project_id)
                report = ProjectReport.objects.create(
                    project=project,
                    title=report_title,
                    content=full_content,
                    report_type=report_type,
                    created_by=request.user
                )
                created_report = report
                
                # Create generated report record
                search_filters = {
                    'query': query,
                    'from_date': from_date,
                    'to_date': to_date,
                    'type_filter': type_filter,
                    'field_filter': field_filter,
                    'report_type': report_type
                }
                
                GeneratedReport.objects.create(
                    project_report=report,
                    query_text=query,
                    from_date=from_date_obj,
                    to_date=to_date_obj,
                    search_filters=search_filters
                )
                
                messages.success(request, 'Project report created successfully.')
                return redirect('project_report_detail', pk=report.pk)
        except (Project.DoesNotExist, ValueError):
            messages.error(request, 'No project found to create a report.')
            return redirect('search_history')
            
    elif type_filter == 'subproject':
        # Try to get the first subproject from the results to associate with this report
        try:
            subproject_id = request.session.get('first_subproject_id')
            if subproject_id:
                subproject = SubProject.objects.get(id=subproject_id)
                report = SubProjectReport.objects.create(
                    subproject=subproject,
                    title=report_title,
                    content=full_content,
                    report_type=report_type,
                    created_by=request.user
                )
                created_report = report
                
                # Create generated report record
                search_filters = {
                    'query': query,
                    'from_date': from_date,
                    'to_date': to_date,
                    'type_filter': type_filter,
                    'field_filter': field_filter,
                    'report_type': report_type
                }
                
                GeneratedReport.objects.create(
                    subproject_report=report,
                    query_text=query,
                    from_date=from_date_obj,
                    to_date=to_date_obj,
                    search_filters=search_filters
                )
                
                messages.success(request, 'Subproject report created successfully.')
                return redirect('subproject_report_detail', pk=report.pk)
        except (SubProject.DoesNotExist, ValueError):
            messages.error(request, 'No subproject found to create a report.')
            return redirect('search_history')
    
    else:
        # For 'all' type, try to create a project report first, then fall back to subproject
        try:
            project_id = request.session.get('first_project_id')
            if project_id:
                project = Project.objects.get(id=project_id)
                report = ProjectReport.objects.create(
                    project=project,
                    title=report_title,
                    content=full_content,
                    report_type=report_type,
                    created_by=request.user
                )
                created_report = report
                
                # Create generated report record
                GeneratedReport.objects.create(
                    project_report=report,
                    query_text=query,
                    from_date=from_date_obj,
                    to_date=to_date_obj
                )
                
                messages.success(request, 'Project report created successfully.')
                return redirect('project_report_detail', pk=report.pk)
            
            subproject_id = request.session.get('first_subproject_id')
            if subproject_id:
                subproject = SubProject.objects.get(id=subproject_id)
                report = SubProjectReport.objects.create(
                    subproject=subproject,
                    title=report_title,
                    content=full_content,
                    report_type=report_type,
                    created_by=request.user
                )
                created_report = report
                
                # Create generated report record
                GeneratedReport.objects.create(
                    subproject_report=report,
                    query_text=query,
                    from_date=from_date_obj,
                    to_date=to_date_obj
                )


                
                messages.success(request, 'Subproject report created successfully.')
                return redirect('subproject_report_detail', pk=report.pk)
                
            # If we get here, we don't have either project or subproject
            messages.error(request, 'No project or subproject found to create a report.')
            return redirect('search_history')
            
        except (Project.DoesNotExist, SubProject.DoesNotExist, ValueError):
            messages.error(request, 'No project or subproject found to create a report.')
            return redirect('search_history')

@login_required
def search_history_view(request):
    """View for searching history"""
    # Check if the user is a province manager or expert - restrict access
    if request.user.is_province_manager or request.user.is_expert:
        messages.error(request, "شما مجوز دسترسی به بخش جستجو را ندارید.")
        return redirect('dashboard:dashboard')
        
    query = request.GET.get('query', '')
    from_date = request.GET.get('from_date', '')
    to_date = request.GET.get('to_date', '')
    type_filter = 'project'  # Always search for projects
    
    # Project-specific filters
    project_types = request.GET.getlist('project_types')
    project_statuses = request.GET.getlist('project_statuses')
    project_provinces = request.GET.getlist('project_provinces')
    approval_statuses = request.GET.getlist('approval_statuses')
    
    # Program-specific filters
    program_types = request.GET.getlist('program_types')
    program_provinces = request.GET.getlist('program_provinces')
    license_states = request.GET.getlist('license_states')
    license_codes = request.GET.getlist('license_codes')
    
    # Estimated opening time filter
    opening_time_filter_enabled = request.GET.get('opening_time_filter_enabled', '')
    opening_time_date = request.GET.get('opening_time_date', '')
    
    # Financial filters - only relevant project financial fields
    cash_allocation_enabled = request.GET.get('cash_allocation_enabled', '')
    min_cash_allocation = request.GET.get('min_cash_allocation', '')
    max_cash_allocation = request.GET.get('max_cash_allocation', '')
    
    # Cash allocation type filters
    cash_national_enabled = request.GET.get('cash_national_enabled', '')
    min_cash_national = request.GET.get('min_cash_national', '')
    max_cash_national = request.GET.get('max_cash_national', '')
    
    cash_province_enabled = request.GET.get('cash_province_enabled', '')
    min_cash_province = request.GET.get('min_cash_province', '')
    max_cash_province = request.GET.get('max_cash_province', '')
    
    cash_charity_enabled = request.GET.get('cash_charity_enabled', '')
    min_cash_charity = request.GET.get('min_cash_charity', '')
    max_cash_charity = request.GET.get('max_cash_charity', '')
    
    cash_travel_enabled = request.GET.get('cash_travel_enabled', '')
    min_cash_travel = request.GET.get('min_cash_travel', '')
    max_cash_travel = request.GET.get('max_cash_travel', '')
    
    treasury_allocation_enabled = request.GET.get('treasury_allocation_enabled', '')
    min_treasury_allocation = request.GET.get('min_treasury_allocation', '')
    max_treasury_allocation = request.GET.get('max_treasury_allocation', '')
    
    # Treasury allocation type filters
    treasury_national_enabled = request.GET.get('treasury_national_enabled', '')
    min_treasury_national = request.GET.get('min_treasury_national', '')
    max_treasury_national = request.GET.get('max_treasury_national', '')
    
    treasury_province_enabled = request.GET.get('treasury_province_enabled', '')
    min_treasury_province = request.GET.get('min_treasury_province', '')
    max_treasury_province = request.GET.get('max_treasury_province', '')
    
    treasury_travel_enabled = request.GET.get('treasury_travel_enabled', '')
    min_treasury_travel = request.GET.get('min_treasury_travel', '')
    max_treasury_travel = request.GET.get('max_treasury_travel', '')
    
    total_allocation_enabled = request.GET.get('total_allocation_enabled', '')
    min_total_allocation = request.GET.get('min_total_allocation', '')
    max_total_allocation = request.GET.get('max_total_allocation', '')
    
    required_credit_enabled = request.GET.get('required_credit_enabled', '')
    min_required_credit = request.GET.get('min_required_credit', '')
    max_required_credit = request.GET.get('max_required_credit', '')
    
    debt_enabled = request.GET.get('debt_enabled', '')
    min_debt = request.GET.get('min_debt', '')
    max_debt = request.GET.get('max_debt', '')
    
    # Physical Progress filter
    min_physical_progress = request.GET.get('min_physical_progress', '')
    max_physical_progress = request.GET.get('max_physical_progress', '')
    
    # Financial Progress filter
    min_financial_progress = request.GET.get('min_financial_progress', '')
    max_financial_progress = request.GET.get('max_financial_progress', '')
    
    # Area Size filter
    min_area_size = request.GET.get('min_area_size', '')
    max_area_size = request.GET.get('max_area_size', '')
    
    # Notables filter
    min_notables = request.GET.get('min_notables', '')
    max_notables = request.GET.get('max_notables', '')
    
    # Floor filter
    min_floor = request.GET.get('min_floor', '')
    max_floor = request.GET.get('max_floor', '')
    
    # Site Area filter
    min_site_area = request.GET.get('min_site_area', '')
    max_site_area = request.GET.get('max_site_area', '')
    
    # Wall Length filter
    min_wall_length = request.GET.get('min_wall_length', '')
    max_wall_length = request.GET.get('max_wall_length', '')
    
    # Initialize project search results
    projects = []
    
    # Add province choices for the form
    province_choices = [
        ('تهران', 'تهران'), ('اصفهان', 'اصفهان'), ('فارس', 'فارس'), 
        ('خراسان رضوی', 'خراسان رضوی'), ('آذربایجان شرقی', 'آذربایجان شرقی'),
        ('آذربایجان غربی', 'آذربایجان غربی'), ('اردبیل', 'اردبیل'),
        ('البرز', 'البرز'), ('ایلام', 'ایلام'), ('بوشهر', 'بوشهر'),
        ('چهارمحال و بختیاری', 'چهارمحال و بختیاری'), ('خراسان جنوبی', 'خراسان جنوبی'),
        ('خراسان شمالی', 'خراسان شمالی'), ('خوزستان', 'خوزستان'),
        ('زنجان', 'زنجان'), ('سمنان', 'سمنان'), ('سیستان و بلوچستان', 'سیستان و بلوچستان'),
        ('قزوین', 'قزوین'), ('قم', 'قم'), ('کردستان', 'کردستان'),
        ('کرمان', 'کرمان'), ('کرمانشاه', 'کرمانشاه'), ('کهگیلویه و بویراحمد', 'کهگیلویه و بویراحمد'),
        ('گلستان', 'گلستان'), ('گیلان', 'گیلان'), ('لرستان', 'لرستان'),
        ('مازندران', 'مازندران'), ('مرکزی', 'مرکزی'), ('هرمزگان', 'هرمزگان'),
        ('همدان', 'همدان'), ('یزد', 'یزد'),("اردبیل", "اردبیل")
    ]
    
    # Project type choices (from Project model)
    project_type_choices = [
        ('احداث', 'احداث'),
        ('تکمیل', 'تکمیل'),
        ('محوطه سازی', 'محوطه سازی'),
        ('دیوار کشی', 'دیوار کشی'),
        ('محوطه سازی و دیوار کشی', 'محوطه سازی و دیوار کشی'),
        ('تعمیرات', 'تعمیرات'),
        ('مشاور فاز یک و دو (طراحی)', 'مشاور فاز یک و دو (طراحی)'),
        ('مشاور فاز سه (نظارت)', 'مشاور فاز سه (نظارت)'),
    ]
    
    # Project status choices
    project_status_choices = [
        ('فعال', 'فعال'),
        ('تامین اعتبار', 'تامین اعتبار'),
        ('غیره فعال', 'غیره فعال'),
    ]
    
    # Program type choices (from Program model)
    program_type_choices = [
        ('پایگاه امداد جاده ای', 'پایگاه امداد جاده ای'),
        ('پایگاه امداد کوهستانی', 'پایگاه امداد کوهستانی'),
        ('پایگاه امداد دریایی', 'پایگاه امداد دریایی'),
        ('ساختمان اداری آموزشی درمانی وفرهنگی', 'ساختمان اداری آموزشی درمانی وفرهنگی'),
        ('پایگاه عملیات پشتیبانی اقماری هوایی', 'پایگاه عملیات پشتیبانی اقماری هوایی'),
        ('مولد سازی', 'مولد سازی'),
        ('سالن چند منظوره/انبار امدادی', 'سالن چند منظوره/انبار امدادی'),
    ]
    
    # License state choices
    license_state_choices = [
        ("دارد", "دارد"),
        ("ندارد", "ندارد"),
        ("دردست اقدام", "دردست اقدام"),
        ("قبل از بخش نامه اردیبهشت 91", "قبل از بخش نامه اردیبهشت 91")
    ]
    
    # Initialize context here before the conditional
    context = {
        'update_history': [],
        'projects': projects,
        'total_project_results': len(projects),
        'province_choices': province_choices,
        'project_type_choices': project_type_choices,
        'project_status_choices': project_status_choices,
        'program_type_choices': program_type_choices,
        'license_state_choices': license_state_choices,
        'type_filter': type_filter,
        'debt_enabled': debt_enabled,
        'query': query,
        'from_date': from_date,
        'to_date': to_date,
        'opening_time_filter_enabled': opening_time_filter_enabled,
        'opening_time_date': opening_time_date,
        'project_city': request.GET.get('project_city', ''),
        'project_name': request.GET.get('project_name', ''),
        'project_id': request.GET.get('project_id', ''),
        'program_title': request.GET.get('program_title', ''),
        'program_id': request.GET.get('program_id', ''),
        'min_physical_progress': min_physical_progress,
        'max_physical_progress': max_physical_progress,
        'min_area_size': min_area_size,
        'max_area_size': max_area_size,
        'min_notables': min_notables,
        'max_notables': max_notables,
        'min_floor': min_floor,
        'max_floor': max_floor,
        'min_site_area': min_site_area,
        'max_site_area': max_site_area,
        'min_wall_length': min_wall_length,
        'max_wall_length': max_wall_length,
        # Financial filters
        'cash_allocation_enabled': cash_allocation_enabled,
        'min_cash_allocation': min_cash_allocation,
        'max_cash_allocation': max_cash_allocation,
        'cash_national_enabled': cash_national_enabled,
        'min_cash_national': min_cash_national, 
        'max_cash_national': max_cash_national,
        'cash_province_enabled': cash_province_enabled,
        'min_cash_province': min_cash_province,
        'max_cash_province': max_cash_province,
        'cash_charity_enabled': cash_charity_enabled, 
        'min_cash_charity': min_cash_charity,
        'max_cash_charity': max_cash_charity,
        'cash_travel_enabled': cash_travel_enabled,
        'min_cash_travel': min_cash_travel,
        'max_cash_travel': max_cash_travel,
        'treasury_allocation_enabled': treasury_allocation_enabled,
        'min_treasury_allocation': min_treasury_allocation,
        'max_treasury_allocation': max_treasury_allocation,
        'treasury_national_enabled': treasury_national_enabled,
        'min_treasury_national': min_treasury_national,
        'max_treasury_national': max_treasury_national,
        'treasury_province_enabled': treasury_province_enabled,
        'min_treasury_province': min_treasury_province,
        'max_treasury_province': max_treasury_province,
        'treasury_travel_enabled': treasury_travel_enabled,
        'min_treasury_travel': min_treasury_travel,
        'max_treasury_travel': max_treasury_travel,
        'total_allocation_enabled': total_allocation_enabled,
        'min_total_allocation': min_total_allocation,
        'max_total_allocation': max_total_allocation,
        'required_credit_enabled': required_credit_enabled,
        'min_required_credit': min_required_credit,
        'max_required_credit': max_required_credit,
        'min_debt': min_debt,
        'max_debt': max_debt,
        # Add missing context variables for template
        'selected_project_types': project_types,
        'selected_project_statuses': project_statuses,
        'selected_project_provinces': project_provinces,
        'selected_approval_statuses': approval_statuses,
        'selected_program_types': program_types,
        'selected_program_provinces': program_provinces,
        'selected_license_states': license_states,
        'selected_license_codes': license_codes,
        'min_financial_progress': min_financial_progress,
        'max_financial_progress': max_financial_progress
    }

    # Only process search if form was submitted (any GET parameter exists)
    if any(request.GET.values()):
        # Base querysets for direct results (not history)
        project_queryset = Project.objects.select_related('program').all().order_by('name')
        
        try:
            # Apply search query if provided
            if query:
                # Split query into words for more flexible searching
                query_words = query.split()
                
                # Start with an empty Q object
                query_filter = Q()
                
                # Add each word as a separate condition - only relevant project and program fields
                for word in query_words:
                    query_filter |= Q(name__icontains=word) | \
                                   Q(project_id__icontains=word) | \
                                   Q(province__icontains=word) | \
                                   Q(city__icontains=word) | \
                                   Q(project_type__icontains=word) | \
                                   Q(overall_status__icontains=word) | \
                                   Q(program__title__icontains=word) | \
                                   Q(program__program_id__icontains=word) | \
                                   Q(program__program_type__icontains=word) | \
                                   Q(program__license_state__icontains=word) | \
                                   Q(program__license_code__icontains=word) | \
                                   Q(program__province__icontains=word) | \
                                   Q(program__city__icontains=word)
                
                project_queryset = project_queryset.filter(query_filter)
            
            # Project name filter
            project_name = request.GET.get('project_name', '')
            if project_name:
                project_queryset = project_queryset.filter(name__icontains=project_name)
                
            # Project ID filter
            project_id = request.GET.get('project_id', '')
            if project_id:
                project_queryset = project_queryset.filter(project_id__icontains=project_id)
            
            # Program title filter
            program_title = request.GET.get('program_title', '')
            if program_title:
                project_queryset = project_queryset.filter(program__title__icontains=program_title)
                
            # Program ID filter
            program_id = request.GET.get('program_id', '')
            if program_id:
                project_queryset = project_queryset.filter(program__program_id__icontains=program_id)
            
            # Project type filter
            if project_types:
                project_queryset = project_queryset.filter(project_type__in=project_types)
            
            # Program type filter
            if program_types:
                project_queryset = project_queryset.filter(program__program_type__in=program_types)
            
            # Project status filter
            if project_statuses:
                project_queryset = project_queryset.filter(overall_status__in=project_statuses)
            
            # Project province filter
            if project_provinces:
                project_queryset = project_queryset.filter(province__in=project_provinces)
            
            # Program province filter
            if program_provinces:
                project_queryset = project_queryset.filter(program__province__in=program_provinces)
            
            # License state filter
            if license_states:
                project_queryset = project_queryset.filter(program__license_state__in=license_states)
            
            # License code filter
            if license_codes:
                project_queryset = project_queryset.filter(program__license_code__in=license_codes)
            
            # City filter
            project_city = request.GET.get('project_city', '')
            if project_city:
                project_queryset = project_queryset.filter(city__icontains=project_city)
            
            # Physical Progress filter
            if min_physical_progress:
                try:
                    min_progress_value = float(min_physical_progress)
                    project_queryset = project_queryset.filter(physical_progress__gte=min_progress_value)
                except ValueError:
                    pass
                    
            if max_physical_progress:
                try:
                    max_progress_value = float(max_physical_progress)
                    project_queryset = project_queryset.filter(physical_progress__lte=max_progress_value)
                except ValueError:
                    pass
            
            # Financial Progress filter
            if min_financial_progress:
                try:
                    min_financial_value = float(min_financial_progress)
                    # Filter projects based on calculated financial progress
                    # We need to calculate financial progress for each project
                    filtered_projects = []
                    for project in project_queryset:
                        financial_progress = project.calculate_financial_progress()
                        if financial_progress >= min_financial_value:
                            filtered_projects.append(project.id)
                    project_queryset = project_queryset.filter(id__in=filtered_projects)
                except ValueError:
                    pass
                    
            if max_financial_progress:
                try:
                    max_financial_value = float(max_financial_progress)
                    # Filter projects based on calculated financial progress
                    filtered_projects = []
                    for project in project_queryset:
                        financial_progress = project.calculate_financial_progress()
                        if financial_progress <= max_financial_value:
                            filtered_projects.append(project.id)
                    project_queryset = project_queryset.filter(id__in=filtered_projects)
                except ValueError:
                    pass
            
            # Area Size filter
            if min_area_size or max_area_size:
                # Handle null values properly
                if min_area_size and max_area_size:
                    try:
                        min_area_value = float(min_area_size)
                        max_area_value = float(max_area_size)
                        project_queryset = project_queryset.filter(
                            area_size__gte=min_area_value,
                            area_size__lte=max_area_value
                        )
                    except ValueError:
                        pass
                elif min_area_size:
                    try:
                        min_area_value = float(min_area_size)
                        project_queryset = project_queryset.filter(area_size__gte=min_area_value)
                    except ValueError:
                        pass
                elif max_area_size:
                    try:
                        max_area_value = float(max_area_size)
                        project_queryset = project_queryset.filter(area_size__lte=max_area_value)
                    except ValueError:
                        pass
            
            # Notables filter
            if min_notables or max_notables:
                # Handle null values properly
                if min_notables and max_notables:
                    try:
                        min_notables_value = float(min_notables)
                        max_notables_value = float(max_notables)
                        project_queryset = project_queryset.filter(
                            notables__gte=min_notables_value,
                            notables__lte=max_notables_value
                        )
                    except ValueError:
                        pass
                elif min_notables:
                    try:
                        min_notables_value = float(min_notables)
                        project_queryset = project_queryset.filter(notables__gte=min_notables_value)
                    except ValueError:
                        pass
                elif max_notables:
                    try:
                        max_notables_value = float(max_notables)
                        project_queryset = project_queryset.filter(notables__lte=max_notables_value)
                    except ValueError:
                        pass
            
            # Floor filter
            if min_floor or max_floor:
                # Handle null values properly
                if min_floor and max_floor:
                    try:
                        min_floor_value = int(min_floor)
                        max_floor_value = int(max_floor)
                        project_queryset = project_queryset.filter(
                            floor__gte=min_floor_value,
                            floor__lte=max_floor_value
                        )
                    except ValueError:
                        pass
                elif min_floor:
                    try:
                        min_floor_value = int(min_floor)
                        project_queryset = project_queryset.filter(floor__gte=min_floor_value)
                    except ValueError:
                        pass
                elif max_floor:
                    try:
                        max_floor_value = int(max_floor)
                        project_queryset = project_queryset.filter(floor__lte=max_floor_value)
                    except ValueError:
                        pass
            
            # Site Area filter
            if min_site_area or max_site_area:
                # Handle null values properly
                if min_site_area and max_site_area:
                    try:
                        min_site_area_value = float(min_site_area)
                        max_site_area_value = float(max_site_area)
                        project_queryset = project_queryset.filter(
                            site_area__gte=min_site_area_value,
                            site_area__lte=max_site_area_value
                        )
                    except ValueError:
                        pass
                elif min_site_area:
                    try:
                        min_site_area_value = float(min_site_area)
                        project_queryset = project_queryset.filter(site_area__gte=min_site_area_value)
                    except ValueError:
                        pass
                elif max_site_area:
                    try:
                        max_site_area_value = float(max_site_area)
                        project_queryset = project_queryset.filter(site_area__lte=max_site_area_value)
                    except ValueError:
                        pass
            
            # Wall Length filter
            if min_wall_length or max_wall_length:
                # Handle null values properly
                if min_wall_length and max_wall_length:
                    try:
                        min_wall_length_value = float(min_wall_length)
                        max_wall_length_value = float(max_wall_length)
                        project_queryset = project_queryset.filter(
                            wall_length__gte=min_wall_length_value,
                            wall_length__lte=max_wall_length_value
                        )
                    except ValueError:
                        pass
                elif min_wall_length:
                    try:
                        min_wall_length_value = float(min_wall_length)
                        project_queryset = project_queryset.filter(wall_length__gte=min_wall_length_value)
                    except ValueError:
                        pass
                elif max_wall_length:
                    try:
                        max_wall_length_value = float(max_wall_length)
                        project_queryset = project_queryset.filter(wall_length__lte=max_wall_length_value)
                    except ValueError:
                        pass
            
            # Opening time filter
            if opening_time_filter_enabled == 'on' and opening_time_date:
                try:
                    # Parse Persian date and convert to Gregorian
                    opening_date_obj = parse_jalali_date(opening_time_date)
                    if opening_date_obj:
                        project_queryset = project_queryset.filter(estimated_opening_time__lte=opening_date_obj)
                except Exception as e:
                    print(f"Error parsing opening time date '{opening_time_date}': {str(e)}")
                    pass
                
            # Approval status filter
            if approval_statuses:
                approval_mapping = {
                    'Approved': True,
                    'Pending Approval': None,
                    'Rejected': False
                }
                
                approval_query = Q()
                for status in approval_statuses:
                    if status in approval_mapping:
                        if approval_mapping[status] is None:
                            approval_query |= Q(is_approved__isnull=True)
                        else:
                            approval_query |= Q(is_approved=approval_mapping[status])
                
                if approval_query:
                    project_queryset = project_queryset.filter(approval_query)
            
            # Cash allocation filters
            if cash_allocation_enabled == 'on':
                # Remove commas from numeric inputs
                min_cash_allocation_clean = min_cash_allocation.replace(',', '') if min_cash_allocation else ''
                max_cash_allocation_clean = max_cash_allocation.replace(',', '') if max_cash_allocation else ''
                
                # Define the expression with proper null handling
                cash_total_expr = (
                    Coalesce(F('allocation_credit_cash_national'), 0) + 
                    Coalesce(F('allocation_credit_cash_province'), 0) + 
                    Coalesce(F('allocation_credit_cash_charity'), 0) + 
                    Coalesce(F('allocation_credit_cash_travel'), 0)
                )
                project_queryset = project_queryset.annotate(total_cash_allocation=cash_total_expr)
                
                if min_cash_allocation_clean:
                    try:
                        min_cash_value = float(min_cash_allocation_clean)
                        project_queryset = project_queryset.filter(total_cash_allocation__gte=min_cash_value)
                    except ValueError:
                        pass
                        
                if max_cash_allocation_clean:
                    try:
                        max_cash_value = float(max_cash_allocation_clean)
                        project_queryset = project_queryset.filter(total_cash_allocation__lte=max_cash_value)
                    except ValueError:
                        pass
            
            # Cash National allocation filters
            if cash_national_enabled == 'on':
                # Clean numeric inputs
                min_cash_national_clean = min_cash_national.replace(',', '') if min_cash_national else ''
                max_cash_national_clean = max_cash_national.replace(',', '') if max_cash_national else ''
                
                # Add annotation for field with null handling
                project_queryset = project_queryset.annotate(
                    cash_national_value=Coalesce(F('allocation_credit_cash_national'), 0)
                )
                
                if min_cash_national_clean:
                    try:
                        min_value = float(min_cash_national_clean)
                        project_queryset = project_queryset.filter(cash_national_value__gte=min_value)
                    except ValueError:
                        pass
                        
                if max_cash_national_clean:
                    try:
                        max_value = float(max_cash_national_clean)
                        project_queryset = project_queryset.filter(cash_national_value__lte=max_value)
                    except ValueError:
                        pass
            
            # Cash Province allocation filters
            if cash_province_enabled == 'on':
                # Clean numeric inputs
                min_cash_province_clean = min_cash_province.replace(',', '') if min_cash_province else ''
                max_cash_province_clean = max_cash_province.replace(',', '') if max_cash_province else ''
                
                # Add annotation for field with null handling
                project_queryset = project_queryset.annotate(
                    cash_province_value=Coalesce(F('allocation_credit_cash_province'), 0)
                )
                
                if min_cash_province_clean:
                    try:
                        min_value = float(min_cash_province_clean)
                        project_queryset = project_queryset.filter(cash_province_value__gte=min_value)
                    except ValueError:
                        pass
                        
                if max_cash_province_clean:
                    try:
                        max_value = float(max_cash_province_clean)
                        project_queryset = project_queryset.filter(cash_province_value__lte=max_value)
                    except ValueError:
                        pass
            
            # Cash Charity allocation filters
            if cash_charity_enabled == 'on':
                # Clean numeric inputs
                min_cash_charity_clean = min_cash_charity.replace(',', '') if min_cash_charity else ''
                max_cash_charity_clean = max_cash_charity.replace(',', '') if max_cash_charity else ''
                
                # Add annotation for field with null handling
                project_queryset = project_queryset.annotate(
                    cash_charity_value=Coalesce(F('allocation_credit_cash_charity'), 0)
                )
                
                if min_cash_charity_clean:
                    try:
                        min_value = float(min_cash_charity_clean)
                        project_queryset = project_queryset.filter(cash_charity_value__gte=min_value)
                    except ValueError:
                        pass
                        
                if max_cash_charity_clean:
                    try:
                        max_value = float(max_cash_charity_clean)
                        project_queryset = project_queryset.filter(cash_charity_value__lte=max_value)
                    except ValueError:
                        pass
            
            # Cash Travel allocation filters
            if cash_travel_enabled == 'on':
                # Clean numeric inputs
                min_cash_travel_clean = min_cash_travel.replace(',', '') if min_cash_travel else ''
                max_cash_travel_clean = max_cash_travel.replace(',', '') if max_cash_travel else ''
                
                # Add annotation for field with null handling
                project_queryset = project_queryset.annotate(
                    cash_travel_value=Coalesce(F('allocation_credit_cash_travel'), 0)
                )
                
                if min_cash_travel_clean:
                    try:
                        min_value = float(min_cash_travel_clean)
                        project_queryset = project_queryset.filter(cash_travel_value__gte=min_value)
                    except ValueError:
                        pass
                        
                if max_cash_travel_clean:
                    try:
                        max_value = float(max_cash_travel_clean)
                        project_queryset = project_queryset.filter(cash_travel_value__lte=max_value)
                    except ValueError:
                        pass
            
            # Treasury allocation filters
            if treasury_allocation_enabled == 'on':
                # Clean numeric inputs
                min_treasury_allocation_clean = min_treasury_allocation.replace(',', '') if min_treasury_allocation else ''
                max_treasury_allocation_clean = max_treasury_allocation.replace(',', '') if max_treasury_allocation else ''
                
                treasury_total_expr = (
                    Coalesce(F('allocation_credit_treasury_national'), 0) + 
                    Coalesce(F('allocation_credit_treasury_province'), 0) + 
                    Coalesce(F('allocation_credit_treasury_travel'), 0)
                )
                project_queryset = project_queryset.annotate(total_treasury_allocation=treasury_total_expr)
                
                if min_treasury_allocation_clean:
                    try:
                        min_treasury_value = float(min_treasury_allocation_clean)
                        project_queryset = project_queryset.filter(total_treasury_allocation__gte=min_treasury_value)
                    except ValueError:
                        pass
                        
                if max_treasury_allocation_clean:
                    try:
                        max_treasury_value = float(max_treasury_allocation_clean)
                        project_queryset = project_queryset.filter(total_treasury_allocation__lte=max_treasury_value)
                    except ValueError:
                        pass
            
            # Treasury National allocation filters
            if treasury_national_enabled == 'on':
                # Clean numeric inputs
                min_treasury_national_clean = min_treasury_national.replace(',', '') if min_treasury_national else ''
                max_treasury_national_clean = max_treasury_national.replace(',', '') if max_treasury_national else ''
                
                # Add annotation for field with null handling
                project_queryset = project_queryset.annotate(
                    treasury_national_value=Coalesce(F('allocation_credit_treasury_national'), 0)
                )
                
                if min_treasury_national_clean:
                    try:
                        min_value = float(min_treasury_national_clean)
                        project_queryset = project_queryset.filter(treasury_national_value__gte=min_value)
                    except ValueError:
                        pass
                        
                if max_treasury_national_clean:
                    try:
                        max_value = float(max_treasury_national_clean)
                        project_queryset = project_queryset.filter(treasury_national_value__lte=max_value)
                    except ValueError:
                        pass
            
            # Treasury Province allocation filters
            if treasury_province_enabled == 'on':
                # Clean numeric inputs
                min_treasury_province_clean = min_treasury_province.replace(',', '') if min_treasury_province else ''
                max_treasury_province_clean = max_treasury_province.replace(',', '') if max_treasury_province else ''
                
                # Add annotation for field with null handling
                project_queryset = project_queryset.annotate(
                    treasury_province_value=Coalesce(F('allocation_credit_treasury_province'), 0)
                )
                
                if min_treasury_province_clean:
                    try:
                        min_value = float(min_treasury_province_clean)
                        project_queryset = project_queryset.filter(treasury_province_value__gte=min_value)
                    except ValueError:
                        pass
                        
                if max_treasury_province_clean:
                    try:
                        max_value = float(max_treasury_province_clean)
                        project_queryset = project_queryset.filter(treasury_province_value__lte=max_value)
                    except ValueError:
                        pass
            
            # Treasury Travel allocation filters
            if treasury_travel_enabled == 'on':
                # Clean numeric inputs
                min_treasury_travel_clean = min_treasury_travel.replace(',', '') if min_treasury_travel else ''
                max_treasury_travel_clean = max_treasury_travel.replace(',', '') if max_treasury_travel else ''
                
                # Add annotation for field with null handling
                project_queryset = project_queryset.annotate(
                    treasury_travel_value=Coalesce(F('allocation_credit_treasury_travel'), 0)
                )
                
                if min_treasury_travel_clean:
                    try:
                        min_value = float(min_treasury_travel_clean)
                        project_queryset = project_queryset.filter(treasury_travel_value__gte=min_value)
                    except ValueError:
                        pass
                        
                if max_treasury_travel_clean:
                    try:
                        max_value = float(max_treasury_travel_clean)
                        project_queryset = project_queryset.filter(treasury_travel_value__lte=max_value)
                    except ValueError:
                        pass
            
            # Total allocation filters (cash + treasury)
            if total_allocation_enabled == 'on':
                # Clean numeric inputs
                min_total_allocation_clean = min_total_allocation.replace(',', '') if min_total_allocation else ''
                max_total_allocation_clean = max_total_allocation.replace(',', '') if max_total_allocation else ''
                
                total_expr = (
                    Coalesce(F('allocation_credit_cash_national'), 0) + 
                    Coalesce(F('allocation_credit_cash_province'), 0) + 
                    Coalesce(F('allocation_credit_cash_charity'), 0) + 
                    Coalesce(F('allocation_credit_cash_travel'), 0) + 
                    Coalesce(F('allocation_credit_treasury_national'), 0) + 
                    Coalesce(F('allocation_credit_treasury_province'), 0) + 
                    Coalesce(F('allocation_credit_treasury_travel'), 0)
                )
                project_queryset = project_queryset.annotate(combined_total_allocation=total_expr)
                
                if min_total_allocation_clean:
                    try:
                        min_total_value = float(min_total_allocation_clean)
                        project_queryset = project_queryset.filter(combined_total_allocation__gte=min_total_value)
                    except ValueError:
                        pass
                        
                if max_total_allocation_clean:
                    try:
                        max_total_value = float(max_total_allocation_clean)
                        project_queryset = project_queryset.filter(combined_total_allocation__lte=max_total_value)
                    except ValueError:
                        pass
            
            # Required credit for project filters
            if required_credit_enabled == 'on':
                # Clean numeric inputs
                min_required_credit_clean = min_required_credit.replace(',', '') if min_required_credit else ''
                max_required_credit_clean = max_required_credit.replace(',', '') if max_required_credit else ''
                
                # Add annotation for field with null handling
                project_queryset = project_queryset.annotate(
                    required_credit_value=Coalesce(F('cached_required_credit_project'), 0)
                )
                
                if min_required_credit_clean:
                    try:
                        min_value = float(min_required_credit_clean)
                        project_queryset = project_queryset.filter(required_credit_value__gte=min_value)
                    except ValueError:
                        pass
                        
                if max_required_credit_clean:
                    try:
                        max_value = float(max_required_credit_clean)
                        project_queryset = project_queryset.filter(required_credit_value__lte=max_value)
                    except ValueError:
                        pass
            
            # Required credit for contracts filters
            if request.GET.get('required_credit_contracts_enabled', '') == 'on':
                # Clean numeric inputs
                min_required_credit_contracts = request.GET.get('min_required_credit_contracts', '').replace(',', '')
                max_required_credit_contracts = request.GET.get('max_required_credit_contracts', '').replace(',', '')
                
                # Add annotation for field with null handling
                project_queryset = project_queryset.annotate(
                    required_credit_contracts_value=Coalesce(F('cached_required_credit_contracts'), 0)
                )
                
                if min_required_credit_contracts:
                    try:
                        min_value = float(min_required_credit_contracts)
                        project_queryset = project_queryset.filter(required_credit_contracts_value__gte=min_value)
                    except ValueError:
                        pass
                        
                if max_required_credit_contracts:
                    try:
                        max_value = float(max_required_credit_contracts)
                        project_queryset = project_queryset.filter(required_credit_contracts_value__lte=max_value)
                    except ValueError:
                        pass
            
            # Debt filters
            if debt_enabled == 'on':
                # Clean numeric inputs
                min_debt_clean = min_debt.replace(',', '') if min_debt else ''
                max_debt_clean = max_debt.replace(',', '') if max_debt else ''
                
                # Add annotation for field with null handling
                project_queryset = project_queryset.annotate(
                    debt_value=Coalesce(F('cached_total_debt'), 0)
                )
                
                if min_debt_clean:
                    try:
                        min_debt_value = float(min_debt_clean)
                        project_queryset = project_queryset.filter(debt_value__gte=min_debt_value)
                    except ValueError:
                        pass
                        
                if max_debt_clean:
                    try:
                        max_debt_value = float(max_debt_clean)
                        project_queryset = project_queryset.filter(debt_value__lte=max_debt_value)
                    except ValueError:
                        pass
            
            # Get the limited fields we need for display after all filtering is done
            projects = project_queryset.values(
                'id', 'name', 'physical_progress', 'province', 'project_type',
                'program__title', 'program__program_id', 'program__program_type',
                'program__license_state', 'program__license_code', 'program__province'
            )
            
            # Add calculated financial progress
            for project in projects:
                project_obj = Project.objects.get(id=project['id'])
                project['financial_progress'] = project_obj.calculate_financial_progress
            
            # Record the search in the user's history
            if projects:
                SearchHistory.objects.create(
                    user=request.user,
                    query_text=query,
                    filters={
                        'type_filter': type_filter,
                        'from_date': from_date,
                        'to_date': to_date,
                        'project_types': project_types,
                        'project_statuses': project_statuses,
                        'project_provinces': project_provinces,
                        'program_types': program_types,
                        'program_provinces': program_provinces,
                        'license_states': license_states,
                        'license_codes': license_codes,
                        'debt_enabled': debt_enabled,
                        'min_debt': min_debt,
                        'max_debt': max_debt,
                        'cash_allocation_enabled': cash_allocation_enabled,
                        'min_cash_allocation': min_cash_allocation,
                        'max_cash_allocation': max_cash_allocation,
                        'treasury_allocation_enabled': treasury_allocation_enabled,
                        'min_treasury_allocation': min_treasury_allocation,
                        'max_treasury_allocation': max_treasury_allocation,
                        'total_allocation_enabled': total_allocation_enabled,
                        'min_total_allocation': min_total_allocation,
                        'max_total_allocation': max_total_allocation,
                        'required_credit_enabled': required_credit_enabled,
                        'min_required_credit': min_required_credit,
                        'max_required_credit': max_required_credit
                    }
                )
                
            # Store counts in session for report generation
            request.session['total_project_results'] = len(projects)
            
            # Store first project ID for report creation
            if projects:
                request.session['first_project_id'] = projects[0]['id']
                
            # Update context with the search results
            context.update({
                'projects': projects,
                'total_project_results': len(projects)
            })
                
        except Exception as e:
            # Log the error but don't crash
            print(f"Error processing search: {str(e)}")
            projects = []
    
    # Always return a response with the correct template
    return render(request, 'reporter/search_history.html', context)

@login_required
def program_search_view(request):
    """View for searching programs (طرح)"""
    # Check if the user is a province manager or expert - restrict access
    if request.user.is_province_manager or request.user.is_expert:
        messages.error(request, "شما مجوز دسترسی به بخش جستجو را ندارید.")
        return redirect('dashboard:dashboard')
        
    query = request.GET.get('query', '')
    from_date = request.GET.get('from_date', '')
    to_date = request.GET.get('to_date', '')
    
    # Program-specific filters
    program_types = request.GET.getlist('program_types')
    program_provinces = request.GET.getlist('program_provinces')
    license_states = request.GET.getlist('license_states')
    license_codes = request.GET.getlist('license_codes')
    
    # Program opening date filter
    opening_date_filter_enabled = request.GET.get('opening_date_enabled', '')
    opening_date = request.GET.get('opening_date', '')
    
    # Initialize program search results
    programs = []
    
    # Add province choices for the form
    province_choices = [
        ('تهران', 'تهران'), ('اصفهان', 'اصفهان'), ('فارس', 'فارس'), 
        ('خراسان رضوی', 'خراسان رضوی'), ('آذربایجان شرقی', 'آذربایجان شرقی'),
        ('آذربایجان غربی', 'آذربایجان غربی'), ('اردبیل', 'اردبیل'),
        ('البرز', 'البرز'), ('ایلام', 'ایلام'), ('بوشهر', 'بوشهر'),
        ('چهارمحال و بختیاری', 'چهارمحال و بختیاری'), ('خراسان جنوبی', 'خراسان جنوبی'),
        ('خراسان شمالی', 'خراسان شمالی'), ('خوزستان', 'خوزستان'),
        ('زنجان', 'زنجان'), ('سمنان', 'سمنان'), ('سیستان و بلوچستان', 'سیستان و بلوچستان'),
        ('قزوین', 'قزوین'), ('قم', 'قم'), ('کردستان', 'کردستان'),
        ('کرمان', 'کرمان'), ('کرمانشاه', 'کرمانشاه'), ('کهگیلویه و بویراحمد', 'کهگیلویه و بویراحمد'),
        ('گلستان', 'گلستان'), ('گیلان', 'گیلان'), ('لرستان', 'لرستان'),
        ('مازندران', 'مازندران'), ('مرکزی', 'مرکزی'), ('هرمزگان', 'هرمزگان'),
        ('همدان', 'همدان'), ('یزد', 'یزد'),("اردبیل", "اردبیل")
    ]
    
    # Program type choices (from Program model)
    program_type_choices = [
        ('پایگاه امداد جاده ای', 'پایگاه امداد جاده ای'),
        ('پایگاه امداد کوهستانی', 'پایگاه امداد کوهستانی'),
        ('پایگاه امداد دریایی', 'پایگاه امداد دریایی'),
        ('ساختمان اداری آموزشی درمانی وفرهنگی', 'ساختمان اداری آموزشی درمانی وفرهنگی'),
        ('پایگاه عملیات پشتیبانی اقماری هوایی', 'پایگاه عملیات پشتیبانی اقماری هوایی'),
        ('مولد سازی', 'مولد سازی'),
        ('سالن چند منظوره/انبار امدادی', 'سالن چند منظوره/انبار امدادی'),
    ]
    
    # License state choices (from Program model)
    license_state_choices = [
        ("دارد", "دارد"),
        ("ندارد", "ندارد"),
        ("دردست اقدام", "دردست اقدام"),
        ("قبل از بخش نامه اردیبهشت 91", "قبل از بخش نامه اردیبهشت 91")
    ]
    
    # Get selected values for form
    selected_program_types = request.GET.getlist('program_types')
    selected_program_provinces = request.GET.getlist('program_provinces')
    selected_license_states = request.GET.getlist('license_states')
    
    # Only process search if form was submitted (any GET parameter exists)
    if any(request.GET.values()):
        # Base queryset for programs
        program_queryset = Program.objects.all().order_by('title')
        
        try:
            # Apply search query if provided
            if query:
                # Split query into words for more flexible searching
                query_words = query.split()
                
                # Start with an empty Q object
                query_filter = Q()
                
                # Add each word as a separate condition
                for word in query_words:
                    query_filter |= Q(title__icontains=word) | \
                                   Q(program_id__icontains=word) | \
                                   Q(province__icontains=word) | \
                                   Q(city__icontains=word) | \
                                   Q(program_type__icontains=word) | \
                                   Q(license_state__icontains=word) | \
                                   Q(license_code__icontains=word)
                
                program_queryset = program_queryset.filter(query_filter)
            
            # Program title filter
            program_title = request.GET.get('program_title', '')
            if program_title:
                program_queryset = program_queryset.filter(title__icontains=program_title)
                
            # Program ID filter
            program_id = request.GET.get('program_id', '')
            if program_id:
                program_queryset = program_queryset.filter(program_id__icontains=program_id)
            
            # Program type filter
            if program_types:
                program_queryset = program_queryset.filter(program_type__in=program_types)
            
            # Program province filter
            if program_provinces:
                program_queryset = program_queryset.filter(province__in=program_provinces)
            
            # License state filter
            if license_states:
                program_queryset = program_queryset.filter(license_state__in=license_states)
            
            # License code filter
            if license_codes:
                program_queryset = program_queryset.filter(license_code__icontains=license_codes[0])
            
            # Program opening date filter
            if opening_date_filter_enabled == 'on' and opening_date:
                try:
                    # Parse Persian date and convert to Gregorian
                    opening_date_obj = parse_jalali_date(opening_date)
                    if opening_date_obj:
                        program_queryset = program_queryset.filter(program_opening_date__lte=opening_date_obj)
                except Exception as e:
                    print(f"Error parsing opening date '{opening_date}': {str(e)}")
                    pass
            
            # Date range filters
            if from_date:
                try:
                    from_date_obj = datetime.strptime(from_date, '%Y-%m-%d').date()
                    program_queryset = program_queryset.filter(created_at__date__gte=from_date_obj)
                except ValueError:
                    pass
            
            if to_date:
                try:
                    to_date_obj = datetime.strptime(to_date, '%Y-%m-%d').date()
                    program_queryset = program_queryset.filter(created_at__date__lte=to_date_obj)
                except ValueError:
                    pass
            
            # Convert queryset to list for template
            programs = list(program_queryset)
            
            # Save search history
            if programs:
                SearchHistory.objects.create(
                    user=request.user,
                    query_text=query,
                    from_date=from_date_obj if from_date else None,
                    to_date=to_date_obj if to_date else None,
                    field_filter='program',
                    search_type='program',
                    results_count=len(programs),
                    filters={
                        'program_types': program_types,
                        'program_provinces': program_provinces,
                        'license_states': license_states,
                        'license_codes': license_codes,
                        'opening_date': opening_date if opening_date_filter_enabled == 'on' else None,
                    }
                )
                
        except Exception as e:
            # Log the error but don't crash
            print(f"Error processing program search: {str(e)}")
            programs = []
    
    context = {
        'programs': programs,
        'query': query,
        'from_date': from_date,
        'to_date': to_date,
        'program_types': program_type_choices,
        'program_provinces': province_choices,
        'license_states': license_state_choices,
        'selected_program_types': selected_program_types,
        'selected_program_provinces': selected_program_provinces,
        'selected_license_states': selected_license_states,
        'opening_date_filter_enabled': opening_date_filter_enabled,
        'opening_date': opening_date,
        'total_program_results': len(programs)
    }
    
    return render(request, 'reporter/program_search.html', context)

@login_required
def user_search_history(request):
    """View for displaying user's search history"""
    searches = SearchHistory.objects.filter(user=request.user).order_by('-timestamp')
    
    context = {
        'searches': searches,
        'recent_project_reports': ProjectReport.objects.filter(created_by=request.user).order_by('-created_at')[:3],
        'recent_subproject_reports': SubProjectReport.objects.filter(created_by=request.user).order_by('-created_at')[:3],
    }
    
    return render(request, 'reporter/user_search_history.html', context)

@login_required
def projects_map_view(request):
    """View for displaying the programs progress map"""
    # Check if the user is a province manager - restrict access
    if request.user.is_province_manager:
        messages.error(request, "شما دسترسی به بخش گزارش گیری را ندارید.")
        return redirect('dashboard:dashboard')
    
    # Import Program model
    from creator_program.models import Program
    
    # Get all programs that have longitude and latitude coordinates
    programs = Program.objects.filter(
        longitude__isnull=False, 
        latitude__isnull=False
    )
    print(f"DEBUG: Initial programs with coordinates: {programs.count()}")
    
    # Filter by province if the user has a province restriction
    user_provinces = request.user.get_assigned_provinces()
    if user_provinces and not (request.user.is_admin or request.user.is_chief_executive or request.user.is_ceo or request.user.is_vice_chief_executive):
        programs = programs.filter(province__in=user_provinces)
        print(f"DEBUG: After province filter ({user_provinces}): {programs.count()}")
    
    # Get request parameters for filtering
    province = request.GET.get('province', '')
    program_type = request.GET.get('program_type', '')
    print(f"DEBUG: Filter params - province: '{province}', program_type: '{program_type}'")
    
    # Apply filters if provided
    if province:
        programs = programs.filter(province=province)
        print(f"DEBUG: After province filter: {programs.count()}")
    if program_type:
        programs = programs.filter(program_type=program_type)
        print(f"DEBUG: After program_type filter: {programs.count()}")
    
    # Prepare data for the map view
    program_data = []
    for program in programs:
        # Get overall progress based on projects in this program
        progress = program.calculate_overall_physical_progress()

        # Prepare the program data for the map
        # Get coordinates directly from program
        longitude = None
        latitude = None
        try:
            longitude = float(program.longitude) if program.longitude else None
            latitude = float(program.latitude) if program.latitude else None
        except (ValueError, TypeError):
            longitude = None
            latitude = None
        
        # Only include programs with valid coordinates
        if longitude is not None and latitude is not None:
            program_info = {
                'id': program.id,
                'name': program.title,
                'longitude': longitude,
                'latitude': latitude,
                'progress': float(progress),
                'province': program.province,
                'city': program.city,
                'type': program.program_type,
                'url': reverse('creator_program:program_detail', kwargs={'pk': program.id})
            }
            program_data.append(program_info)
    
    print(f"DEBUG: Final program_data count: {len(program_data)}")
    print(f"DEBUG: User: {request.user.username}, Role: {request.user.role}, Assigned Provinces: {request.user.get_assigned_provinces()}")
    
    # Prepare JSON for frontend
    programs_json = json.dumps(program_data, ensure_ascii=False)
    
    # Get unique provinces and program types for filters
    provinces = Program.PROVINCE_CHOICES
    program_types = Program.PROGRAM_TYPE_CHOICES
    
    context = {
        'programs': program_data,
        'programs_json': programs_json,
        'provinces': provinces,
        'program_types': program_types,
        'selected_province': province,
        'selected_type': program_type
    }
    
    return render(request, 'reporter/projects_map.html', context)

@login_required
def export_projects_excel(request):
    # Get project IDs from request
    project_ids_param = request.GET.get('project_ids', '')
    if not project_ids_param:
        return HttpResponse('No projects selected for export', status=400)
    
    # Parse project IDs
    try:
        project_ids = [int(pid) for pid in project_ids_param.split(',') if pid]
    except ValueError:
        return HttpResponse('Invalid project ID format', status=400)
    
    if not project_ids:
        return HttpResponse('No valid project IDs provided', status=400)
    
    # Fetch projects
    projects = Project.objects.filter(id__in=project_ids)
    
    # Create an in-memory output file for the Excel
    output = BytesIO()
    
    # Create a workbook and add a worksheet
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet('گزارش پروژه‌ها')
    
    # Add formatting
    header_format = workbook.add_format({
        'bold': True,
        'font_size': 12,
        'align': 'center',
        'valign': 'vcenter',
        'bg_color': '#4F81BD',
        'font_color': 'white',
        'border': 1
    })
    
    cell_format = workbook.add_format({
        'font_size': 11,
        'align': 'center',
        'valign': 'vcenter',
        'border': 1
    })
    
    number_format = workbook.add_format({
        'font_size': 11,
        'align': 'center',
        'valign': 'vcenter',
        'border': 1,
        'num_format': '#,##0'  # Format for numbers with thousands separator
    })
    
    # Define headers
    headers = [
        'کد پروژه', 'نام پروژه', 'استان', 'شهر', 'نوع پروژه', 'وضعیت مجوز', 'کد مجوز', 'تا تاریخ افتتاح طرح میشود',
        'عرصه', 'اعیان', 'طبقه', 'پیشرفت فیزیکی', 'پیشرفت مالی', 'مجموع دیون',
        'اعتبار مورد نیاز تکمیل قرار داد ها', 'اعتبار مورد نیاز تکمیل پروژه', 'مجموع تخصیص‌ها',
        'تاریخ پایان پروژه', 'مجموع تخصیص‌ها ی اعتبار نقدی نوع ملی', 'مجموع تخصیص‌ها ی اعتبار نقدی نوع استانی',
        'مجموع تخصیص‌ها ی اعتبار نقدی نوع خیریه', 'مجموع تخصیص‌ها ی اعتبار نقدی نوع سفر',
        'مجموع تخصیص‌ها ی اعتبار اسناد خزانه نوع ملی', 'مجموع تخصیص‌ها ی اعتبار اسناد خزانه نوع استانی',
        'مجموع تخصیص‌ها ی اعتبار اسناد خزانه نوع سفر'
    ]
    
    # Set the column widths
    for col_num, header in enumerate(headers):
        worksheet.set_column(col_num, col_num, 18)
    
    # Write the headers
    for col_num, header in enumerate(headers):
        worksheet.write(0, col_num, header, header_format)
    
    # Write data rows
    for row_num, project in enumerate(projects, 1):
        estimated_opening_time = project.estimated_opening_time.strftime('%Y-%m-%d') if project.estimated_opening_time else ''
        
        # Calculate total allocations - handle null values
        total_cash_allocation = (
            (project.allocation_credit_cash_national or 0) +
            (project.allocation_credit_cash_province or 0) +
            (project.allocation_credit_cash_charity or 0) + 
            (project.allocation_credit_cash_travel or 0)
        )
        
        total_treasury_allocation = (
            (project.allocation_credit_treasury_national or 0) +
            (project.allocation_credit_treasury_province or 0) +
            (project.allocation_credit_treasury_travel or 0)
        )
        
        total_allocation = total_cash_allocation + total_treasury_allocation
        
        # Get financial progress
        financial_progress = project.calculate_financial_progress()
        
        # Write text columns
        worksheet.write(row_num, 0, project.project_id, cell_format)
        worksheet.write(row_num, 1, project.name, cell_format)
        worksheet.write(row_num, 2, project.province, cell_format)
        worksheet.write(row_num, 3, project.city, cell_format)
        worksheet.write(row_num, 4, project.project_type, cell_format)
        # Access license fields through the program relationship
        license_state = project.program.license_state if project.program else ''
        license_code = project.program.license_code if project.program else ''
        program_opening_date = project.program.program_opening_date.strftime('%Y-%m-%d') if project.program and project.program.program_opening_date else ''
        worksheet.write(row_num, 5, license_state, cell_format)
        worksheet.write(row_num, 6, license_code, cell_format)
        worksheet.write(row_num, 7, program_opening_date, cell_format)
        
        # Write numeric columns with proper format and null handling
        worksheet.write(row_num, 8, float(project.area_size or 0) if project.area_size else 0, number_format)
        worksheet.write(row_num, 9, float(project.notables or 0) if project.notables else 0, number_format)
        worksheet.write(row_num, 10, project.floor if project.floor else '', cell_format)
        worksheet.write(row_num, 11, float(project.physical_progress or 0), number_format)
        worksheet.write(row_num, 12, financial_progress or 0, number_format)
        worksheet.write(row_num, 14, float(project.cached_total_debt or 0), number_format)
        worksheet.write(row_num, 15, float(project.cached_required_credit_contracts or 0), number_format)
        worksheet.write(row_num, 16, float(project.cached_required_credit_project or 0), number_format)
        worksheet.write(row_num, 17, float(total_allocation), number_format)
        worksheet.write(row_num, 18, estimated_opening_time, cell_format)
        worksheet.write(row_num, 19, float(project.allocation_credit_cash_national or 0), number_format)
        worksheet.write(row_num, 20, float(project.allocation_credit_cash_province or 0), number_format)
        worksheet.write(row_num, 21, float(project.allocation_credit_cash_charity or 0), number_format)
        worksheet.write(row_num, 22, float(project.allocation_credit_cash_travel or 0), number_format)
        worksheet.write(row_num, 23, float(project.allocation_credit_treasury_national or 0), number_format)
        worksheet.write(row_num, 24, float(project.allocation_credit_treasury_province or 0), number_format)
        worksheet.write(row_num, 25, float(project.allocation_credit_treasury_travel or 0), number_format)
    
    # Close the workbook
    workbook.close()
    
    # Create the HTTP response with Excel content
    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    
    # Set the filename with current date
    now = datetime.now()
    filename = f"project_report_{now.strftime('%Y%m%d_%H%M')}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response

@login_required
def export_search_results_excel(request):
    """Export search results to Excel based on search parameters"""
    if request.method != 'POST':
        return HttpResponse('Method not allowed', status=405)
    
    # Get search parameters from POST data
    query = request.POST.get('query', '')
    from_date = request.POST.get('from_date', '')
    to_date = request.POST.get('to_date', '')
    
    # Project-specific filters
    project_id = request.POST.get('project_id', '')
    project_name = request.POST.get('project_name', '')
    project_city = request.POST.get('project_city', '')
    project_provinces = request.POST.get('project_provinces', '')
    min_physical_progress = request.POST.get('min_physical_progress', '')
    max_physical_progress = request.POST.get('max_physical_progress', '')
    min_financial_progress = request.POST.get('min_financial_progress', '')
    max_financial_progress = request.POST.get('max_financial_progress', '')
    min_area_size = request.POST.get('min_area_size', '')
    max_area_size = request.POST.get('max_area_size', '')
    min_notables = request.POST.get('min_notables', '')
    max_notables = request.POST.get('max_notables', '')
    min_floor = request.POST.get('min_floor', '')
    max_floor = request.POST.get('max_floor', '')
    min_site_area = request.POST.get('min_site_area', '')
    max_site_area = request.POST.get('max_site_area', '')
    min_wall_length = request.POST.get('min_wall_length', '')
    max_wall_length = request.POST.get('max_wall_length', '')
    project_status = request.POST.get('project_status', '')
    project_types = request.POST.get('project_types', '')
    program_types = request.POST.get('program_types', '')
    license_states = request.POST.get('license_states', '')
    program_province = request.POST.get('program_province', '')
    opening_time_filter_enabled = request.POST.get('opening_time_filter_enabled', '')
    opening_time_date = request.POST.get('opening_time_date', '')
    
    # Financial filters
    cash_allocation_enabled = request.POST.get('cash_allocation_enabled', '')
    min_cash_allocation = request.POST.get('min_cash_allocation', '')
    max_cash_allocation = request.POST.get('max_cash_allocation', '')
    cash_national_enabled = request.POST.get('cash_national_enabled', '')
    min_cash_national = request.POST.get('min_cash_national', '')
    max_cash_national = request.POST.get('max_cash_national', '')
    cash_province_enabled = request.POST.get('cash_province_enabled', '')
    min_cash_province = request.POST.get('min_cash_province', '')
    max_cash_province = request.POST.get('max_cash_province', '')
    cash_charity_enabled = request.POST.get('cash_charity_enabled', '')
    min_cash_charity = request.POST.get('min_cash_charity', '')
    max_cash_charity = request.POST.get('max_cash_charity', '')
    cash_travel_enabled = request.POST.get('cash_travel_enabled', '')
    min_cash_travel = request.POST.get('min_cash_travel', '')
    max_cash_travel = request.POST.get('max_cash_travel', '')
    treasury_allocation_enabled = request.POST.get('treasury_allocation_enabled', '')
    min_treasury_allocation = request.POST.get('min_treasury_allocation', '')
    max_treasury_allocation = request.POST.get('max_treasury_allocation', '')
    treasury_national_enabled = request.POST.get('treasury_national_enabled', '')
    min_treasury_national = request.POST.get('min_treasury_national', '')
    max_treasury_national = request.POST.get('max_treasury_national', '')
    treasury_province_enabled = request.POST.get('treasury_province_enabled', '')
    min_treasury_province = request.POST.get('min_treasury_province', '')
    max_treasury_province = request.POST.get('max_treasury_province', '')
    treasury_travel_enabled = request.POST.get('treasury_travel_enabled', '')
    min_treasury_travel = request.POST.get('min_treasury_travel', '')
    max_treasury_travel = request.POST.get('max_treasury_travel', '')
    total_allocation_enabled = request.POST.get('total_allocation_enabled', '')
    min_total_allocation = request.POST.get('min_total_allocation', '')
    max_total_allocation = request.POST.get('max_total_allocation', '')
    required_credit_enabled = request.POST.get('required_credit_enabled', '')
    min_required_credit = request.POST.get('min_required_credit', '')
    max_required_credit = request.POST.get('max_required_credit', '')
    total_debt_enabled = request.POST.get('total_debt_enabled', '')
    min_total_debt = request.POST.get('min_total_debt', '')
    max_total_debt = request.POST.get('max_total_debt', '')
    required_credit_contracts_enabled = request.POST.get('required_credit_contracts_enabled', '')
    min_required_credit_contracts = request.POST.get('min_required_credit_contracts', '')
    max_required_credit_contracts = request.POST.get('max_required_credit_contracts', '')
    
    # Get selected fields for Excel export
    excel_fields = request.POST.getlist('excel_fields')
    
    if not excel_fields:
        return HttpResponse('No fields selected for export', status=400)
    
    # Build the queryset using the same logic as search_history_view
    project_queryset = Project.objects.select_related('program').all().order_by('name')
    
    try:
        # Apply search query if provided
        if query:
            query_words = query.split()
            query_filter = Q()
            
            for word in query_words:
                query_filter |= Q(name__icontains=word) | \
                               Q(project_id__icontains=word) | \
                               Q(province__icontains=word) | \
                               Q(city__icontains=word) | \
                               Q(project_type__icontains=word) | \
                               Q(overall_status__icontains=word) | \
                               Q(program__title__icontains=word) | \
                               Q(program__program_id__icontains=word) | \
                               Q(program__program_type__icontains=word) | \
                               Q(program__license_state__icontains=word) | \
                               Q(program__license_code__icontains=word) | \
                               Q(program__province__icontains=word) | \
                               Q(program__city__icontains=word)
            
            project_queryset = project_queryset.filter(query_filter)
        
        # Apply individual filters
        if project_name:
            project_queryset = project_queryset.filter(name__icontains=project_name)
        
        if project_id:
            project_queryset = project_queryset.filter(project_id__icontains=project_id)
        
        if project_city:
            project_queryset = project_queryset.filter(city__icontains=project_city)
        
        if project_provinces:
            project_queryset = project_queryset.filter(province__in=project_provinces.split(','))
        
        if project_status:
            project_queryset = project_queryset.filter(overall_status=project_status)
        
        if project_types:
            project_queryset = project_queryset.filter(project_type__in=project_types.split(','))
        
        if program_types:
            project_queryset = project_queryset.filter(program__program_type__in=program_types.split(','))
        
        if license_states:
            project_queryset = project_queryset.filter(program__license_state__in=license_states.split(','))
        
        if program_province:
            project_queryset = project_queryset.filter(program__province=program_province)
        
        # Physical progress filter
        if min_physical_progress or max_physical_progress:
            if min_physical_progress and max_physical_progress:
                project_queryset = project_queryset.filter(
                    physical_progress__gte=float(min_physical_progress),
                    physical_progress__lte=float(max_physical_progress)
                )
            elif min_physical_progress:
                project_queryset = project_queryset.filter(physical_progress__gte=float(min_physical_progress))
            elif max_physical_progress:
                project_queryset = project_queryset.filter(physical_progress__lte=float(max_physical_progress))
        
        # Financial progress filter
        if min_financial_progress or max_financial_progress:
            # Filter projects based on calculated financial progress
            filtered_projects = []
            for project in project_queryset:
                financial_progress = project.calculate_financial_progress()
                include_project = True
                
                if min_financial_progress:
                    try:
                        min_financial_value = float(min_financial_progress)
                        if financial_progress < min_financial_value:
                            include_project = False
                    except ValueError:
                        pass
                
                if max_financial_progress and include_project:
                    try:
                        max_financial_value = float(max_financial_progress)
                        if financial_progress > max_financial_value:
                            include_project = False
                    except ValueError:
                        pass
                
                if include_project:
                    filtered_projects.append(project.id)
            
            project_queryset = project_queryset.filter(id__in=filtered_projects)
        
        # Area Size filter
        if min_area_size or max_area_size:
            # Handle null values properly
            if min_area_size and max_area_size:
                try:
                    min_area_value = float(min_area_size)
                    max_area_value = float(max_area_size)
                    project_queryset = project_queryset.filter(
                        area_size__gte=min_area_value,
                        area_size__lte=max_area_value
                    )
                except ValueError:
                    pass
            elif min_area_size:
                try:
                    min_area_value = float(min_area_size)
                    project_queryset = project_queryset.filter(area_size__gte=min_area_value)
                except ValueError:
                    pass
            elif max_area_size:
                try:
                    max_area_value = float(max_area_size)
                    project_queryset = project_queryset.filter(area_size__lte=max_area_value)
                except ValueError:
                    pass
        
        # Notables filter
        if min_notables or max_notables:
            # Handle null values properly
            if min_notables and max_notables:
                try:
                    min_notables_value = float(min_notables)
                    max_notables_value = float(max_notables)
                    project_queryset = project_queryset.filter(
                        notables__gte=min_notables_value,
                        notables__lte=max_notables_value
                    )
                except ValueError:
                    pass
            elif min_notables:
                try:
                    min_notables_value = float(min_notables)
                    project_queryset = project_queryset.filter(notables__gte=min_notables_value)
                except ValueError:
                    pass
            elif max_notables:
                try:
                    max_notables_value = float(max_notables)
                    project_queryset = project_queryset.filter(notables__lte=max_notables_value)
                except ValueError:
                    pass
        
        # Floor filter
        if min_floor or max_floor:
            # Handle null values properly
            if min_floor and max_floor:
                try:
                    min_floor_value = int(min_floor)
                    max_floor_value = int(max_floor)
                    project_queryset = project_queryset.filter(
                        floor__gte=min_floor_value,
                        floor__lte=max_floor_value
                    )
                except ValueError:
                    pass
            elif min_floor:
                try:
                    min_floor_value = int(min_floor)
                    project_queryset = project_queryset.filter(floor__gte=min_floor_value)
                except ValueError:
                    pass
            elif max_floor:
                try:
                    max_floor_value = int(max_floor)
                    project_queryset = project_queryset.filter(floor__lte=max_floor_value)
                except ValueError:
                    pass
        
        # Opening date filter
        if opening_time_filter_enabled == 'on' and opening_time_date:
            try:
                # Parse Persian date and convert to Gregorian
                opening_date_obj = parse_jalali_date(opening_time_date)
                if opening_date_obj:
                    project_queryset = project_queryset.filter(estimated_opening_time__lte=opening_date_obj)
            except Exception as e:
                print(f"Error parsing opening time date '{opening_time_date}': {str(e)}")
                pass
        
        # Financial filters
        if cash_allocation_enabled == 'on':
            total_cash_allocation_filter = Q()
            if min_cash_allocation:
                total_cash_allocation_filter &= Q(
                    allocation_credit_cash_national__gte=float(min_cash_allocation) / 4
                )
            if max_cash_allocation:
                total_cash_allocation_filter &= Q(
                    allocation_credit_cash_national__lte=float(max_cash_allocation) / 4
                )
            project_queryset = project_queryset.filter(total_cash_allocation_filter)
        
        # Apply other financial filters similarly...
        # (Add all the financial filters logic here)
        
        # Get the final results
        projects = list(project_queryset)
        
        if not projects:
            return HttpResponse('No projects found matching the search criteria', status=400)
        
        # Create Excel file
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('گزارش پروژه‌ها')
        
        # Add formatting
        main_header_format = workbook.add_format({
            'bold': True,
            'font_size': 14,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#2c3e50',
            'font_color': 'white',
            'border': 1,
            'text_wrap': True
        })
        
        sub_header_format = workbook.add_format({
            'bold': True,
            'font_size': 12,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#34495e',
            'font_color': 'white',
            'border': 1,
            'text_wrap': True
        })
        
        field_header_format = workbook.add_format({
            'bold': True,
            'font_size': 11,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#5d6d7e',
            'font_color': 'white',
            'border': 1,
            'text_wrap': True
        })
        
        cell_format = workbook.add_format({
            'font_size': 11,
            'align': 'center',
            'valign': 'vcenter',
            'border': 1
        })
        
        number_format = workbook.add_format({
            'font_size': 11,
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'num_format': '#,##0'
        })
        
        # Define field categories and their headers
        field_categories = {
            'project_info': {
                'main_header': 'اطلاعات پروژه',
                'fields': {
                    'project_id': 'کد پروژه',
                    'project_name': 'نام پروژه',
                    'project_province': 'استان پروژه',
                    'project_city': 'شهر پروژه',
                    'project_type': 'نوع پروژه',
                    'project_status': 'وضعیت پروژه',
                    'physical_progress': 'پیشرفت فیزیکی',
                    'financial_progress': 'پیشرفت مالی',
                    'area_size': 'عرصه',
                    'site_area': 'مساحت محوطه سازی',
                    'wall_length': 'طول دیوار کشی',
                    'notables': 'اعیان',
                    'floor': 'طبقه',
                    'project_opening_date': 'تا تاریخ افتتاح پروژه میشود'
                }
            },
            'program_info': {
                'main_header': 'اطلاعات طرح',
                'fields': {
                    'program_id': 'کد طرح',
                    'program_title': 'عنوان طرح',
                    'program_type': 'نوع طرح',
                    'program_province': 'استان طرح',
                    'license_state': 'وضعیت مجوز'
                }
            },
            'financial_info': {
                'main_header': 'اطلاعات مالی',
                'fields': {
                    'cash_allocation': 'مجموع تخصیص مالی نقدی',
                    'cash_national': 'تخصیص نقدی ملی',
                    'cash_province': 'تخصیص نقدی استانی',
                    'cash_charity': 'تخصیص نقدی خیریه',
                    'cash_travel': 'تخصیص نقدی سفر',
                    'treasury_allocation': 'مجموع تخصیص اسناد خزانه',
                    'treasury_national': 'تخصیص خزانه ملی',
                    'treasury_province': 'تخصیص خزانه استانی',
                    'treasury_travel': 'تخصیص خزانه سفر',
                    'total_allocation': 'مجموع تخصیص مالی',
                    'required_credit': 'اعتبار مورد نیاز تکمیل پروژه',
                    'required_credit_contracts': 'اعتبار مورد نیاز تکمیل قراردادها',
                    'total_debt': 'مجموع دیون'
                }
            }
        }
        
        # Organize selected fields by category
        selected_fields_by_category = {}
        for field in excel_fields:
            for category, category_info in field_categories.items():
                if field in category_info['fields']:
                    if category not in selected_fields_by_category:
                        selected_fields_by_category[category] = []
                    selected_fields_by_category[category].append(field)
                    break
        
        # Write headers (3 rows: main category, sub-category, field names)
        current_col = 0
        
        # Row 1: Main category headers
        for category, fields in selected_fields_by_category.items():
            if fields:  # Only if category has selected fields
                category_info = field_categories[category]
                worksheet.merge_range(0, current_col, 0, current_col + len(fields) - 1, 
                                   category_info['main_header'], main_header_format)
                current_col += len(fields)
        
        # Row 2: Sub-category headers (empty for now, but can be used for sub-categories)
        current_col = 0
        for category, fields in selected_fields_by_category.items():
            if fields:
                for field in fields:
                    worksheet.write(1, current_col, '', sub_header_format)
                    current_col += 1
        
        # Row 3: Field names
        current_col = 0
        for category, fields in selected_fields_by_category.items():
            if fields:
                for field in fields:
                    category_info = field_categories[category]
                    field_name = category_info['fields'][field]
                    worksheet.write(2, current_col, field_name, field_header_format)
                    current_col += 1
        
        # Write data rows (starting from row 4)
        for row_num, project in enumerate(projects, 3):
            current_col = 0
            
            for category, fields in selected_fields_by_category.items():
                if fields:
                    for field in fields:
                        if field == 'project_id':
                            worksheet.write(row_num, current_col, project.project_id or '', cell_format)
                        elif field == 'project_name':
                            worksheet.write(row_num, current_col, project.name or '', cell_format)
                        elif field == 'project_province':
                            worksheet.write(row_num, current_col, project.province or '', cell_format)
                        elif field == 'project_city':
                            worksheet.write(row_num, current_col, project.city or '', cell_format)
                        elif field == 'project_type':
                            worksheet.write(row_num, current_col, project.project_type or '', cell_format)
                        elif field == 'project_status':
                            worksheet.write(row_num, current_col, project.overall_status or '', cell_format)
                        elif field == 'physical_progress':
                            worksheet.write(row_num, current_col, float(project.physical_progress or 0), number_format)
                        elif field == 'financial_progress':
                            financial_progress = project.calculate_financial_progress()
                            worksheet.write(row_num, current_col, float(financial_progress), number_format)
                        elif field == 'area_size':
                            worksheet.write(row_num, current_col, float(project.area_size or 0), number_format)
                        elif field == 'notables':
                            worksheet.write(row_num, current_col, float(project.notables or 0), number_format)
                        elif field == 'floor':
                            worksheet.write(row_num, current_col, int(project.floor or 0), number_format)
                        elif field == 'project_opening_date':
                            opening_date = project.estimated_opening_time.strftime('%Y-%m-%d') if project.estimated_opening_time else ''
                            worksheet.write(row_num, current_col, opening_date, cell_format)
                        elif field == 'program_id':
                            worksheet.write(row_num, current_col, project.program.program_id if project.program else '', cell_format)
                        elif field == 'program_title':
                            worksheet.write(row_num, current_col, project.program.title if project.program else '', cell_format)
                        elif field == 'program_type':
                            worksheet.write(row_num, current_col, project.program.program_type if project.program else '', cell_format)
                        elif field == 'program_province':
                            worksheet.write(row_num, current_col, project.program.province if project.program else '', cell_format)
                        elif field == 'license_state':
                            worksheet.write(row_num, current_col, project.program.license_state if project.program else '', cell_format)
                        elif field == 'cash_allocation':
                            total_cash = (
                                (project.allocation_credit_cash_national or 0) +
                                (project.allocation_credit_cash_province or 0) +
                                (project.allocation_credit_cash_charity or 0) +
                                (project.allocation_credit_cash_travel or 0)
                            )
                            worksheet.write(row_num, current_col, float(total_cash), number_format)
                        elif field == 'cash_national':
                            worksheet.write(row_num, current_col, float(project.allocation_credit_cash_national or 0), number_format)
                        elif field == 'cash_province':
                            worksheet.write(row_num, current_col, float(project.allocation_credit_cash_province or 0), number_format)
                        elif field == 'cash_charity':
                            worksheet.write(row_num, current_col, float(project.allocation_credit_cash_charity or 0), number_format)
                        elif field == 'cash_travel':
                            worksheet.write(row_num, current_col, float(project.allocation_credit_cash_travel or 0), number_format)
                        elif field == 'treasury_allocation':
                            total_treasury = (
                                (project.allocation_credit_treasury_national or 0) +
                                (project.allocation_credit_treasury_province or 0) +
                                (project.allocation_credit_treasury_travel or 0)
                            )
                            worksheet.write(row_num, current_col, float(total_treasury), number_format)
                        elif field == 'treasury_national':
                            worksheet.write(row_num, current_col, float(project.allocation_credit_treasury_national or 0), number_format)
                        elif field == 'treasury_province':
                            worksheet.write(row_num, current_col, float(project.allocation_credit_treasury_province or 0), number_format)
                        elif field == 'treasury_travel':
                            worksheet.write(row_num, current_col, float(project.allocation_credit_treasury_travel or 0), number_format)
                        elif field == 'total_allocation':
                            total_allocation = (
                                (project.allocation_credit_cash_national or 0) +
                                (project.allocation_credit_cash_province or 0) +
                                (project.allocation_credit_cash_charity or 0) +
                                (project.allocation_credit_cash_travel or 0) +
                                (project.allocation_credit_treasury_national or 0) +
                                (project.allocation_credit_treasury_province or 0) +
                                (project.allocation_credit_treasury_travel or 0)
                            )
                            worksheet.write(row_num, current_col, float(total_allocation), number_format)
                        elif field == 'required_credit':
                            worksheet.write(row_num, current_col, float(project.cached_required_credit_project or 0), number_format)
                        elif field == 'required_credit_contracts':
                            worksheet.write(row_num, current_col, float(project.cached_required_credit_contracts or 0), number_format)
                        elif field == 'total_debt':
                            worksheet.write(row_num, current_col, float(project.cached_total_debt or 0), number_format)
                        
                        current_col += 1
        
        # Set column widths for better readability
        for col in range(len(excel_fields)):
            worksheet.set_column(col, col, 15)  # Set width to 15 characters
        
        # Close the workbook
        workbook.close()
        
        # Create the HTTP response
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
        # Set the filename with current date
        now = datetime.now()
        filename = f"project_search_results_{now.strftime('%Y%m%d_%H%M')}.xlsx"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except Exception as e:
        return HttpResponse(f'Error generating Excel file: {str(e)}', status=500)


@login_required
def export_program_search_results_excel(request):
    """Export program search results to Excel based on search parameters"""
    if request.method != 'POST':
        return HttpResponse('Method not allowed', status=405)
    
    # Get search parameters from POST data
    query = request.POST.get('query', '')
    
    # Program-specific filters
    program_title = request.POST.get('program_title', '')
    program_id = request.POST.get('program_id', '')
    program_types = request.POST.getlist('program_types')
    program_provinces = request.POST.getlist('program_provinces')
    license_states = request.POST.getlist('license_states')
    license_codes = request.POST.get('license_codes', '')
    opening_date = request.POST.get('opening_date', '')
    
    # Get selected fields for Excel export
    excel_fields = request.POST.getlist('excel_fields')
    
    if not excel_fields:
        return HttpResponse('No fields selected for export', status=400)
    
    # Build the queryset using the same logic as program_search_view
    program_queryset = Program.objects.all().order_by('title')
    
    try:
        # Apply search query if provided
        if query:
            query_words = query.split()
            query_filter = Q()
            
            for word in query_words:
                query_filter |= Q(title__icontains=word) | \
                               Q(program_id__icontains=word) | \
                               Q(province__icontains=word) | \
                               Q(city__icontains=word) | \
                               Q(program_type__icontains=word) | \
                               Q(license_state__icontains=word) | \
                               Q(license_code__icontains=word)
            
            program_queryset = program_queryset.filter(query_filter)
        
        # Program title filter
        if program_title:
            program_queryset = program_queryset.filter(title__icontains=program_title)
            
        # Program ID filter
        if program_id:
            program_queryset = program_queryset.filter(program_id__icontains=program_id)
        
        # Program type filter
        if program_types:
            program_queryset = program_queryset.filter(program_type__in=program_types)
        
        # Program province filter
        if program_provinces:
            program_queryset = program_queryset.filter(province__in=program_provinces)
        
        # License state filter
        if license_states:
            program_queryset = program_queryset.filter(license_state__in=license_states)
        
        # License code filter
        if license_codes:
            program_queryset = program_queryset.filter(license_code__icontains=license_codes)
        
        # Program opening date filter
        if opening_date:
            try:
                # Parse Persian date and convert to Gregorian
                opening_date_obj = parse_jalali_date(opening_date)
                if opening_date_obj:
                    program_queryset = program_queryset.filter(program_opening_date__lte=opening_date_obj)
            except Exception as e:
                print(f"Error parsing opening date '{opening_date}': {str(e)}")
                pass
        

        
        # Convert queryset to list
        programs = list(program_queryset)
        
        # Create Excel file
        import xlsxwriter
        from io import BytesIO
        
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        
        # Create formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#34495e',
            'font_color': 'white',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter'
        })
        
        cell_format = workbook.add_format({
            'border': 1,
            'align': 'right',
            'valign': 'vcenter'
        })
        
        number_format = workbook.add_format({
            'border': 1,
            'align': 'right',
            'valign': 'vcenter',
            'num_format': '#,##0'
        })
        
        date_format = workbook.add_format({
            'border': 1,
            'align': 'right',
            'valign': 'vcenter',
            'num_format': 'yyyy/mm/dd'
        })
        
        # Create worksheet
        worksheet = workbook.add_worksheet('نتایج جستجوی طرح‌ها')
        
        # Write headers
        for col, field in enumerate(excel_fields):
            field_labels = {
                'title': 'عنوان طرح',
                'program_id': 'کد طرح',
                'program_type': 'نوع طرح',
                'province': 'استان',
                'city': 'شهر',
                'address': 'آدرس',
                'license_state': 'وضعیت مجوز',
                'license_code': 'کد مجوز',
                'program_opening_date': 'تا تاریخ افتتاح طرح میشود',
                'description': 'توضیحات',
                'created_at': 'تاریخ ایجاد',
                'updated_at': 'تاریخ بروزرسانی',
                'is_approved': 'تایید شده',
                'is_submitted': 'ارسال شده',
                'is_expert_approved': 'تایید کارشناس',
                'longitude': 'طول جغرافیایی',
                'latitude': 'عرض جغرافیایی',
            }
            worksheet.write(0, col, field_labels.get(field, field), header_format)
        
        # Write data
        for row_num, program in enumerate(programs, start=1):
            current_col = 0
            for field in excel_fields:
                if field == 'title':
                    worksheet.write(row_num, current_col, program.title or '', cell_format)
                elif field == 'program_id':
                    worksheet.write(row_num, current_col, program.program_id or '', cell_format)
                elif field == 'program_type':
                    worksheet.write(row_num, current_col, program.program_type or '', cell_format)
                elif field == 'province':
                    worksheet.write(row_num, current_col, program.province or '', cell_format)
                elif field == 'city':
                    worksheet.write(row_num, current_col, program.city or '', cell_format)
                elif field == 'address':
                    worksheet.write(row_num, current_col, program.address or '', cell_format)
                elif field == 'license_state':
                    worksheet.write(row_num, current_col, program.license_state or '', cell_format)
                elif field == 'license_code':
                    worksheet.write(row_num, current_col, program.license_code or '', cell_format)
                elif field == 'program_opening_date':
                    if program.program_opening_date:
                        worksheet.write(row_num, current_col, program.program_opening_date, date_format)
                    else:
                        worksheet.write(row_num, current_col, '', cell_format)
                elif field == 'description':
                    worksheet.write(row_num, current_col, program.description or '', cell_format)
                elif field == 'created_at':
                    worksheet.write(row_num, current_col, program.created_at.date(), date_format)
                elif field == 'updated_at':
                    worksheet.write(row_num, current_col, program.updated_at.date(), date_format)
                elif field == 'is_approved':
                    worksheet.write(row_num, current_col, 'بله' if program.is_approved else 'خیر', cell_format)
                elif field == 'is_submitted':
                    worksheet.write(row_num, current_col, 'بله' if program.is_submitted else 'خیر', cell_format)
                elif field == 'is_expert_approved':
                    worksheet.write(row_num, current_col, 'بله' if program.is_expert_approved else 'خیر', cell_format)
                elif field == 'longitude':
                    worksheet.write(row_num, current_col, float(program.longitude or 0), number_format)
                elif field == 'latitude':
                    worksheet.write(row_num, current_col, float(program.latitude or 0), number_format)
                
                current_col += 1
        
        # Set column widths for better readability
        for col in range(len(excel_fields)):
            worksheet.set_column(col, col, 15)  # Set width to 15 characters
        
        # Close the workbook
        workbook.close()
        
        # Create the HTTP response
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
        # Set the filename with current date
        now = datetime.now()
        filename = f"program_search_results_{now.strftime('%Y%m%d_%H%M')}.xlsx"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except Exception as e:
        return HttpResponse(f'Error generating Excel file: {str(e)}', status=500)


