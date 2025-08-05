from django.contrib import admin
from .models import WebhookEvent, WebhookConfiguration


@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    list_display = ['event_type', 'repository', 'branch', 'status', 'created_at']
    list_filter = ['event_type', 'status', 'created_at']
    search_fields = ['repository', 'commit_message', 'event_id']
    readonly_fields = ['event_id', 'created_at', 'updated_at', 'processed_at']
    fieldsets = (
        ('Event Information', {
            'fields': ('event_type', 'event_id', 'repository', 'branch', 'commit_sha', 'commit_message')
        }),
        ('Status', {
            'fields': ('status', 'processed_at', 'error_message')
        }),
        ('Payload', {
            'fields': ('payload',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return False  # Webhook events are created automatically


@admin.register(WebhookConfiguration)
class WebhookConfigurationAdmin(admin.ModelAdmin):
    list_display = ['repository_url', 'is_active', 'auto_deploy', 'deploy_branch', 'created_at']
    list_filter = ['is_active', 'auto_deploy', 'created_at']
    search_fields = ['repository_url']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if 'secret_token' in form.base_fields:
            form.base_fields['secret_token'].widget.attrs['type'] = 'password'
        return form
