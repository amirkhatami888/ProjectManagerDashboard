from django.contrib import admin

from .models import SecuritySettings


@admin.register(SecuritySettings)
class SecuritySettingsAdmin(admin.ModelAdmin):
    list_display = ('id', 'turnstile_enabled', 'brute_force_enabled', 'updated_at')
    readonly_fields = ('updated_at',)
    fields = ('turnstile_enabled', 'brute_force_enabled', 'updated_at')

    def has_add_permission(self, request):
        return not SecuritySettings.objects.exists()
