from django.db import models
from django.conf import settings
from creator_project.models import Project
from creator_subproject.models import SubProject

class ProjectReview(models.Model):
    """Model to track reviews of projects by experts."""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='expert_reviews')
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='expert_project_reviews')
    date_reviewed = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)
    comments = models.TextField(blank=True)
    
    # Review criteria fields
    technical_score = models.PositiveSmallIntegerField(default=0, help_text="امتیاز فنی (0-100)")
    financial_score = models.PositiveSmallIntegerField(default=0, help_text="امتیاز مالی (0-100)")
    schedule_score = models.PositiveSmallIntegerField(default=0, help_text="امتیاز زمان‌بندی (0-100)")
    scope_score = models.PositiveSmallIntegerField(default=0, help_text="امتیاز محدوده (0-100)")
    
    @property
    def total_score(self):
        """Calculate the total score as an average of all score fields."""
        scores = [self.technical_score, self.financial_score, 
                 self.schedule_score, self.scope_score]
        return sum(scores) / len(scores)
    
    def __str__(self):
        return f"بررسی {self.project.name} توسط {self.reviewer.username}"
    
    class Meta:
        verbose_name = "بررسی پروژه"
        verbose_name_plural = "بررسی‌های پروژه"
        ordering = ['-date_reviewed']

class SubProjectReview(models.Model):
    """Model to track reviews of subprojects by experts."""
    subproject = models.ForeignKey(SubProject, on_delete=models.CASCADE, related_name='expert_reviews')
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='expert_subproject_reviews')
    date_reviewed = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)
    comments = models.TextField(blank=True)
    
    # Review criteria fields
    technical_score = models.PositiveSmallIntegerField(default=0, help_text="امتیاز فنی (0-100)")
    financial_score = models.PositiveSmallIntegerField(default=0, help_text="امتیاز مالی (0-100)")
    schedule_score = models.PositiveSmallIntegerField(default=0, help_text="امتیاز زمان‌بندی (0-100)")
    execution_score = models.PositiveSmallIntegerField(default=0, help_text="امتیاز اجرایی (0-100)")
    
    @property
    def total_score(self):
        """Calculate the total score as an average of all score fields."""
        scores = [self.technical_score, self.financial_score, 
                 self.schedule_score, self.execution_score]
        return sum(scores) / len(scores)
    
    def __str__(self):
        return f"بررسی زیرپروژه {self.subproject.sub_project_number} توسط {self.reviewer.username}"
    
    class Meta:
        verbose_name = "بررسی زیرپروژه"
        verbose_name_plural = "بررسی‌های زیرپروژه"
        ordering = ['-date_reviewed']
