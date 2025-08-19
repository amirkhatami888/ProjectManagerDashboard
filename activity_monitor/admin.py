from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    ActivityLog, ProjectChangeLog, UserSession, SystemEvent, 
    ActivityDashboard, AuditTrail
)


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = [
        'timestamp', 'user', 'activity_type', 'description', 
        'ip_address', 'severity', 'is_system_event'
    ]
    list_filter = [
        'activity_type', 'severity', 'is_system_event', 
        'timestamp', 'user'
    ]
    search_fields = ['description', 'user__username', 'user__email', 'ip_address']
    readonly_fields = ['id', 'timestamp', 'session_key', 'ip_address', 'user_agent']
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'timestamp', 'user', 'session_key')
        }),
        ('Activity Details', {
            'fields': ('activity_type', 'description', 'details', 'severity')
        }),
        ('Related Object', {
            'fields': ('content_type', 'object_id'),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ('ip_address', 'user_agent', 'is_system_event'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'content_type')


@admin.register(ProjectChangeLog)
class ProjectChangeLogAdmin(admin.ModelAdmin):
    list_display = [
        'timestamp', 'user', 'project_name', 'change_type', 
        'field_name', 'change_description'
    ]
    list_filter = [
        'change_type', 'timestamp', 'user', 'related_object_type'
    ]
    search_fields = [
        'project_name', 'project_id', 'change_description', 
        'user__username', 'field_name'
    ]
    readonly_fields = ['id', 'timestamp']
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'timestamp', 'user')
        }),
        ('Project Information', {
            'fields': ('project_id', 'project_name')
        }),
        ('Change Details', {
            'fields': ('change_type', 'field_name', 'old_value', 'new_value', 'change_description')
        }),
        ('Related Objects', {
            'fields': ('related_object_type', 'related_object_id'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'login_time', 'logout_time', 'is_active', 
        'ip_address', 'page_views', 'last_activity'
    ]
    list_filter = ['is_active', 'login_time', 'user']
    search_fields = ['user__username', 'user__email', 'ip_address', 'session_key']
    readonly_fields = ['id', 'session_key', 'login_time', 'last_activity']
    date_hierarchy = 'login_time'
    
    fieldsets = (
        ('Session Information', {
            'fields': ('id', 'user', 'session_key', 'is_active')
        }),
        ('Timing', {
            'fields': ('login_time', 'logout_time', 'last_activity')
        }),
        ('Activity Statistics', {
            'fields': ('page_views',)
        }),
        ('Connection Details', {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(SystemEvent)
class SystemEventAdmin(admin.ModelAdmin):
    list_display = [
        'timestamp', 'event_type', 'title', 'severity', 
        'component', 'is_resolved', 'resolved_by'
    ]
    list_filter = [
        'event_type', 'severity', 'is_resolved', 'component', 'timestamp'
    ]
    search_fields = ['title', 'description', 'error_code', 'component']
    readonly_fields = ['id', 'timestamp']
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Event Information', {
            'fields': ('id', 'timestamp', 'event_type', 'title', 'description')
        }),
        ('Technical Details', {
            'fields': ('error_code', 'stack_trace', 'details'),
            'classes': ('collapse',)
        }),
        ('Impact Assessment', {
            'fields': ('component', 'severity')
        }),
        ('Resolution', {
            'fields': ('is_resolved', 'resolved_by', 'resolved_at', 'resolution_notes')
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('resolved_by')


@admin.register(ActivityDashboard)
class ActivityDashboardAdmin(admin.ModelAdmin):
    list_display = [
        'date', 'total_activities', 'total_logins', 'active_users',
        'projects_created', 'projects_updated', 'errors_count'
    ]
    list_filter = ['date']
    readonly_fields = ['id', 'date', 'last_updated']
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'date', 'last_updated')
        }),
        ('Activity Statistics', {
            'fields': ('total_activities', 'total_logins', 'total_project_changes', 'total_system_events')
        }),
        ('User Statistics', {
            'fields': ('active_users', 'new_users')
        }),
        ('Project Statistics', {
            'fields': ('projects_created', 'projects_updated', 'projects_approved', 'projects_rejected')
        }),
        ('System Health', {
            'fields': ('errors_count', 'warnings_count')
        }),
        ('Performance Metrics', {
            'fields': ('avg_response_time', 'peak_concurrent_users'),
            'classes': ('collapse',)
        }),
    )


@admin.register(AuditTrail)
class AuditTrailAdmin(admin.ModelAdmin):
    list_display = [
        'timestamp', 'user', 'operation', 'resource_type', 
        'resource_id', 'requires_approval', 'approved_by'
    ]
    list_filter = [
        'operation', 'resource_type', 'requires_approval', 
        'timestamp', 'user'
    ]
    search_fields = [
        'operation', 'resource_type', 'resource_id', 
        'user__username', 'session_id'
    ]
    readonly_fields = ['id', 'timestamp', 'ip_address', 'user_agent', 'session_id']
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Audit Information', {
            'fields': ('id', 'timestamp', 'user', 'operation')
        }),
        ('Resource Details', {
            'fields': ('resource_type', 'resource_id')
        }),
        ('State Changes', {
            'fields': ('before_state', 'after_state'),
            'classes': ('collapse',)
        }),
        ('Context Information', {
            'fields': ('ip_address', 'user_agent', 'session_id'),
            'classes': ('collapse',)
        }),
        ('Approval Workflow', {
            'fields': ('requires_approval', 'approved_by', 'approved_at')
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'approved_by')


# Custom admin site configuration
admin.site.site_header = "Project Manager Dashboard - Activity Monitor"
admin.site.site_title = "Activity Monitor Admin"
admin.site.index_title = "Activity Monitoring Dashboard"
