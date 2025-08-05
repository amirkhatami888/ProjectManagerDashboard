from django.contrib import admin
from django.utils.html import format_html
from .models import Project, ALL_Project, FundingRequest

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        'name', 
        'created_by', 
        'province', 
        'project_type', 
        'physical_progress', 
        'is_approved'
    )
    list_filter = ('province', 'project_type', 'is_approved')
    search_fields = ('name', 'project_id', 'city')
    readonly_fields = ('project_id', 'created_by', 'created_at', 'updated_at')
    
    def total_budget(self, obj):
        return f"{obj.allocation_credit_cash_national or 0:,} IRR"
    total_budget.short_description = 'Budget'

@admin.register(ALL_Project)
class ALL_ProjectAdmin(admin.ModelAdmin):
    list_display = (
        'name', 
        'province', 
        'city', 
        'project_type', 
        'physical_progress', 
        'is_approved'
    )
    list_filter = ('province', 'project_type', 'is_approved')
    search_fields = ('name', 'province', 'city')
    readonly_fields = ('name', 'province', 'city', 'project_type', 'physical_progress', 'created_by', 'created_at')

@admin.register(FundingRequest)
class FundingRequestAdmin(admin.ModelAdmin):
    list_display = (
        'project', 
        'created_by', 
        'status', 
        'province_suggested_amount', 
        'headquarters_suggested_amount', 
        'final_amount', 
        'created_at'
    )
    list_filter = ('status', 'created_at', 'project__province')
    search_fields = ('project__name', 'project__project_id', 'created_by__username')
    readonly_fields = ('created_at', 'updated_at', 'submitted_at', 'approved_at', 'archived_at')
    
    def amount(self, obj):
        return f"{obj.province_suggested_amount or 0:,} IRR"
    amount.short_description = 'Suggested Amount'
