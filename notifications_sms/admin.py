from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import SMSProvider, SMSTemplate, SMSLog, SMSSettings

@admin.register(SMSProvider)
class SMSProviderAdmin(admin.ModelAdmin):
    list_display = ('name', 'base_url', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)
    
    def save_model(self, request, obj, form, change):
        if obj.is_active:
            # Deactivate all other providers
            SMSProvider.objects.exclude(pk=obj.pk).update(is_active=False)
        super().save_model(request, obj, form, change)

@admin.register(SMSTemplate)
class SMSTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'created_by', 'is_default')
    list_filter = ('type', 'is_default')
    search_fields = ('name', 'content')
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating a new object
            obj.created_by = request.user
        if obj.is_default:
            # Make sure only one template per type is default
            SMSTemplate.objects.filter(type=obj.type).exclude(pk=obj.pk).update(is_default=False)
        super().save_model(request, obj, form, change)

@admin.register(SMSLog)
class SMSLogAdmin(admin.ModelAdmin):
    list_display = ('recipient_number', 'recipient_user', 'sender', 'status', 'sent_at')
    list_filter = ('status', 'sent_at')
    search_fields = ('recipient_number', 'recipient_user__username', 'message')
    readonly_fields = ('sender', 'recipient_number', 'recipient_user', 'message', 
                       'template', 'status', 'error_message', 'sent_at', 'provider')

@admin.register(SMSSettings)
class SMSSettingsAdmin(admin.ModelAdmin):
    list_display = ('provider', 'outdated_project_days', 'not_examined_days')
    
    def has_add_permission(self, request):
        # Only allow adding if no settings object exists
        return not SMSSettings.objects.exists()
        
    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion of the settings object
        return False
