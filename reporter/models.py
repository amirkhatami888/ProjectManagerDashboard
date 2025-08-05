from django.db import models
from django.conf import settings
from creator_project.models import Project
from creator_subproject.models import SubProject

class ProjectReport(models.Model):
    """Model for storing project reports"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='reports')
    title = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_reports')
    content = models.TextField()
    
    REPORT_TYPES = (
        ('financial', 'گزارش مالی'),
        ('progress', 'گزارش پیشرفت'),
        ('issues', 'گزارش مشکلات'),
        ('summary', 'گزارش خلاصه'),
    )
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    
    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'گزارش پروژه'
        verbose_name_plural = 'گزارش‌های پروژه'

class SubProjectReport(models.Model):
    """Model for storing subproject reports"""
    subproject = models.ForeignKey(SubProject, on_delete=models.CASCADE, related_name='reports')
    title = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_subproject_reports')
    content = models.TextField()
    
    REPORT_TYPES = (
        ('financial', 'گزارش مالی'),
        ('progress', 'گزارش پیشرفت'),
        ('issues', 'گزارش مشکلات'),
        ('summary', 'گزارش خلاصه'),
    )
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    
    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'گزارش زیرپروژه'
        verbose_name_plural = 'گزارش‌های زیرپروژه'

class SearchHistory(models.Model):
    """Model for tracking user search history"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='search_history')
    query_text = models.CharField(max_length=255, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    from_date = models.DateField(blank=True, null=True)
    to_date = models.DateField(blank=True, null=True)
    field_filter = models.CharField(max_length=100, blank=True, null=True)
    
    SEARCH_TYPES = (
        ('all', 'همه'),
        ('project', 'پروژه'),
        ('subproject', 'زیرپروژه'),
    )
    search_type = models.CharField(max_length=20, choices=SEARCH_TYPES, default='all')
    results_count = models.IntegerField(default=0)
    
    # New field to store all filters in a structured way
    filters = models.JSONField(default=dict, blank=True, help_text='All search filters in JSON format')
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'تاریخچه جستجو'
        verbose_name_plural = 'تاریخچه‌های جستجو'
    
    def __str__(self):
        return f"{self.query_text} - {self.user.username} - {self.timestamp.strftime('%Y-%m-%d')}"

class GeneratedReport(models.Model):
    """Model for tracking reports generated from search results"""
    project_report = models.ForeignKey(ProjectReport, on_delete=models.SET_NULL, null=True, blank=True, related_name='search_generated')
    subproject_report = models.ForeignKey(SubProjectReport, on_delete=models.SET_NULL, null=True, blank=True, related_name='search_generated')
    created_at = models.DateTimeField(auto_now_add=True)
    query_text = models.CharField(max_length=255, blank=True, null=True)
    from_date = models.DateField(blank=True, null=True)
    to_date = models.DateField(blank=True, null=True)
    
    # New field to store search parameters used to generate this report
    search_filters = models.JSONField(default=dict, blank=True, help_text='Search filters used to generate this report')
    
    class Meta:
        verbose_name = 'گزارش تولید شده از جستجو'
        verbose_name_plural = 'گزارش‌های تولید شده از جستجو'
        ordering = ['-created_at']
    
    def __str__(self):
        if self.project_report:
            return f"گزارش پروژه: {self.project_report.title}"
        elif self.subproject_report:
            return f"گزارش زیرپروژه: {self.subproject_report.title}"
        return "گزارش بدون عنوان"

class ProjectFinancialAllocation(models.Model):
    """Model for tracking financial allocations for projects"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='financial_allocations')
    amount = models.DecimalField(max_digits=12, decimal_places=0)
    allocation_date = models.DateField()
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-allocation_date']
        verbose_name = 'تخصیص مالی پروژه'
        verbose_name_plural = 'تخصیص‌های مالی پروژه'
    
    def __str__(self):
        return f"{self.project.name} - {self.amount} - {self.allocation_date}"
