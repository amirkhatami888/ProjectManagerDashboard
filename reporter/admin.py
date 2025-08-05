from django.contrib import admin
from .models import ProjectReport, SubProjectReport, SearchHistory, GeneratedReport

@admin.register(ProjectReport)
class ProjectReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'report_type', 'created_by', 'created_at')
    list_filter = ('report_type', 'created_at')
    search_fields = ('title', 'content', 'project__title')
    readonly_fields = ('created_at',)

@admin.register(SubProjectReport)
class SubProjectReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'subproject', 'report_type', 'created_by', 'created_at')
    list_filter = ('report_type', 'created_at')
    search_fields = ('title', 'content', 'subproject__title')
    readonly_fields = ('created_at',)

@admin.register(SearchHistory)
class SearchHistoryAdmin(admin.ModelAdmin):
    list_display = ('query_text', 'user', 'search_type', 'results_count', 'timestamp')
    list_filter = ('search_type', 'timestamp', 'results_count')
    search_fields = ('query_text', 'user__username', 'field_filter')
    readonly_fields = ('timestamp',)

@admin.register(GeneratedReport)
class GeneratedReportAdmin(admin.ModelAdmin):
    list_display = ('get_report_title', 'get_report_type', 'get_user', 'created_at')
    list_filter = ('created_at',)
    readonly_fields = ('created_at',)
    
    def get_report_title(self, obj):
        if obj.project_report:
            return obj.project_report.title
        elif obj.subproject_report:
            return obj.subproject_report.title
        return "بدون عنوان"
    get_report_title.short_description = 'عنوان گزارش'
    
    def get_report_type(self, obj):
        if obj.project_report:
            return "گزارش پروژه"
        elif obj.subproject_report:
            return "گزارش زیرپروژه"
        return "نامشخص"
    get_report_type.short_description = 'نوع گزارش'
    
    def get_user(self, obj):
        if obj.project_report:
            return obj.project_report.created_by.username
        elif obj.subproject_report:
            return obj.subproject_report.created_by.username
        return "نامشخص"
    get_user.short_description = 'کاربر'
