from django.contrib import admin
from .models import Program, ProgramUpdateHistory, ProgramRejectionComment


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ['title', 'program_id', 'program_type', 'license_state', 'created_by', 'created_at', 'is_approved']
    list_filter = ['program_type', 'license_state', 'is_approved', 'is_submitted', 'created_at']
    search_fields = ['title', 'program_id', 'license_code']
    readonly_fields = ['program_id', 'created_at', 'updated_at', 'program_opening_date']
    ordering = ['-created_at']
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('title', 'program_id', 'program_type', 'description')
        }),
        ('اطلاعات مجوز', {
            'fields': ('license_state', 'license_code')
        }),
        ('تاریخ افتتاح طرح', {
            'fields': ('program_opening_date',),
            'description': 'این تاریخ به صورت خودکار بر اساس آخرین تاریخ پایان پروژه‌های این طرح محاسبه می‌شود'
        }),
        ('وضعیت', {
            'fields': ('is_approved', 'is_submitted', 'is_expert_approved')
        }),
        ('اطلاعات سیستم', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating a new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ProgramUpdateHistory)
class ProgramUpdateHistoryAdmin(admin.ModelAdmin):
    list_display = ['program', 'field_name', 'updated_by', 'updated_at']
    list_filter = ['field_name', 'updated_at']
    search_fields = ['program__title', 'program__program_id']
    readonly_fields = ['program', 'updated_by', 'updated_at', 'field_name', 'old_value', 'new_value']
    ordering = ['-updated_at']


@admin.register(ProgramRejectionComment)
class ProgramRejectionCommentAdmin(admin.ModelAdmin):
    list_display = ['program', 'field_name', 'expert', 'created_at', 'is_resolved']
    list_filter = ['field_name', 'is_resolved', 'created_at']
    search_fields = ['program__title', 'program__program_id', 'expert__username']
    readonly_fields = ['created_at']
    ordering = ['-created_at']