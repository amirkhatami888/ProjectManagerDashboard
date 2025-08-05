from django.db import models
from django.utils import timezone
import json


class WebhookEvent(models.Model):
    """Model to store incoming webhook events"""
    EVENT_TYPES = [
        ('push', 'Push'),
        ('pull_request', 'Pull Request'),
        ('issues', 'Issues'),
        ('release', 'Release'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES, default='other')
    event_id = models.CharField(max_length=100, unique=True)
    repository = models.CharField(max_length=200)
    branch = models.CharField(max_length=100, blank=True, null=True)
    commit_sha = models.CharField(max_length=40, blank=True, null=True)
    commit_message = models.TextField(blank=True, null=True)
    payload = models.JSONField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    processed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.event_type} - {self.repository} - {self.created_at}"
    
    def mark_as_processing(self):
        self.status = 'processing'
        self.save()
    
    def mark_as_completed(self):
        self.status = 'completed'
        self.processed_at = timezone.now()
        self.save()
    
    def mark_as_failed(self, error_message):
        self.status = 'failed'
        self.error_message = error_message
        self.processed_at = timezone.now()
        self.save()


class WebhookConfiguration(models.Model):
    """Model to store webhook configuration settings"""
    repository_url = models.URLField()
    secret_token = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    auto_deploy = models.BooleanField(default=True)
    deploy_branch = models.CharField(max_length=100, default='main')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Webhook Configuration'
        verbose_name_plural = 'Webhook Configurations'
    
    def __str__(self):
        return f"Webhook for {self.repository_url}"
