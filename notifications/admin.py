from django.contrib import admin
from .models import (
    SMSSettings, 
    RejectionSMSSettings, 
    ExpertReminderSMSSettings,
    SMSLog,
    ProjectExpertNotification
)

@admin.register(SMSSettings)
class SMSSettingsAdmin(admin.ModelAdmin):
    list_display = ('enabled', 'sender_number', 'inactivity_days', 'last_run')
    readonly_fields = ('last_run',)
    fieldsets = (
        ('تنظیمات اصلی', {
            'fields': ('enabled', 'api_key', 'sender_number', 'inactivity_days')
        }),
        ('قالب پیام', {
            'fields': ('message_template',),
            'description': 'از {project_name} برای نمایش نام پروژه استفاده کنید.'
        }),
        ('اطلاعات سیستمی', {
            'fields': ('last_run',),
            'classes': ('collapse',),
        }),
    )

    def has_add_permission(self, request):
        # Check if settings already exist
        if SMSSettings.objects.exists():
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(RejectionSMSSettings)
class RejectionSMSSettingsAdmin(admin.ModelAdmin):
    list_display = ('enabled', 'last_run')
    readonly_fields = ('last_run',)

@admin.register(ExpertReminderSMSSettings)
class ExpertReminderSMSSettingsAdmin(admin.ModelAdmin):
    list_display = ('enabled', 'reminder_days', 'last_run')
    readonly_fields = ('last_run',)

@admin.register(SMSLog)
class SMSLogAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'project_name', 'province', 'sent_at', 'status')
    list_filter = ('status', 'province', 'sent_at')
    search_fields = ('recipient__username', 'project_name', 'project_id')
    readonly_fields = ('sent_at', 'message_id', 'error_message')

@admin.register(ProjectExpertNotification)
class ProjectExpertNotificationAdmin(admin.ModelAdmin):
    list_display = ('project', 'expert', 'notification_type', 'created_at', 'is_read', 'notified_via_sms')
    list_filter = ('notification_type', 'is_read', 'notified_via_sms', 'created_at')
    search_fields = ('project__name', 'expert__username')
    readonly_fields = ('created_at',)
