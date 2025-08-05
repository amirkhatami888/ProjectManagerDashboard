from django.contrib import admin
from .models import ProjectReview, SubProjectReview

@admin.register(ProjectReview)
class ProjectReviewAdmin(admin.ModelAdmin):
    list_display = ('project', 'reviewer', 'is_approved', 'date_reviewed', 'total_score')
    list_filter = ('is_approved', 'date_reviewed')
    search_fields = ('project__name', 'reviewer__username', 'comments')
    readonly_fields = ('date_reviewed',)

@admin.register(SubProjectReview)
class SubProjectReviewAdmin(admin.ModelAdmin):
    list_display = ('subproject', 'reviewer', 'is_approved', 'date_reviewed', 'total_score')
    list_filter = ('is_approved', 'date_reviewed')
    search_fields = ('subproject__name', 'reviewer__username', 'comments')
    readonly_fields = ('date_reviewed',)
