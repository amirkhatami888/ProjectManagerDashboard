from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder
import json
import uuid
from datetime import timedelta


class ActivityLog(models.Model):
    """
    Main model for tracking all user activities and system events
    """
    ACTIVITY_TYPES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('VIEW', 'View'),
        ('DOWNLOAD', 'Download'),
        ('UPLOAD', 'Upload'),
        ('APPROVE', 'Approve'),
        ('REJECT', 'Reject'),
        ('SUBMIT', 'Submit'),
        ('ASSIGN', 'Assign'),
        ('COMMENT', 'Comment'),
        ('NOTIFICATION', 'Notification'),
        ('SYSTEM', 'System Event'),
    ]
    
    # Basic information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='activity_logs')
    session_key = models.CharField(max_length=40, blank=True, null=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    
    # Activity details
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    description = models.TextField()
    details = models.JSONField(default=dict, encoder=DjangoJSONEncoder, blank=True)
    
    # Related object (generic foreign key)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Additional metadata
    is_system_event = models.BooleanField(default=False)
    severity = models.CharField(max_length=10, choices=[
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ], default='LOW')
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['activity_type', 'timestamp']),
            models.Index(fields=['content_type', 'object_id']),
        ]
    
    def __str__(self):
        return f"{self.activity_type} by {self.user} at {self.timestamp}"


class ProjectChangeLog(models.Model):
    """
    Specific model for tracking project-related changes in detail
    """
    CHANGE_TYPES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('STATUS', 'Status Change'),
        ('FINANCIAL', 'Financial Change'),
        ('PROGRESS', 'Progress Update'),
        ('ASSIGNMENT', 'Assignment Change'),
        ('REVIEW', 'Review Update'),
        ('FUNDING', 'Funding Change'),
        ('DOCUMENT', 'Document Change'),
        ('METADATA', 'Metadata Change'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Project reference
    project_id = models.CharField(max_length=50, db_index=True)  # Project ID from creator_project
    project_name = models.CharField(max_length=255)
    
    # Change details
    change_type = models.CharField(max_length=20, choices=CHANGE_TYPES)
    field_name = models.CharField(max_length=100, blank=True)  # Persian label
    original_field_name = models.CharField(max_length=100, blank=True)  # Original field name
    old_value = models.TextField(blank=True, null=True)
    new_value = models.TextField(blank=True, null=True)
    change_description = models.TextField()
    
    # Additional context
    related_object_type = models.CharField(max_length=50, blank=True)  # e.g., 'SubProject', 'FundingRequest'
    related_object_id = models.CharField(max_length=50, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['project_id', 'timestamp']),
            models.Index(fields=['change_type', 'timestamp']),
            models.Index(fields=['user', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.change_type} for {self.project_name} at {self.timestamp}"


class UserSession(models.Model):
    """
    Track user sessions for monitoring user activity patterns
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sessions')
    session_key = models.CharField(max_length=40, unique=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    login_time = models.DateTimeField(default=timezone.now)
    logout_time = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    # Session statistics
    page_views = models.PositiveIntegerField(default=0)
    last_activity = models.DateTimeField(default=timezone.now)
    
    # Session timeout (15 minutes default)
    SESSION_TIMEOUT_MINUTES = 15
    
    class Meta:
        ordering = ['-login_time']
    
    def __str__(self):
        return f"Session {self.session_key} for {self.user}"
    
    @property
    def is_online(self):
        """Check if user is currently online based on session timeout"""
        if not self.is_active:
            return False
        
        # Check if session has timed out (15 minutes of inactivity)
        timeout_threshold = timezone.now() - timedelta(minutes=self.SESSION_TIMEOUT_MINUTES)
        return self.last_activity > timeout_threshold
    
    @property
    def session_duration(self):
        """Get current session duration"""
        if self.logout_time:
            return self.logout_time - self.login_time
        else:
            return timezone.now() - self.login_time
    
    @property
    def time_since_last_activity(self):
        """Get time since last activity"""
        return timezone.now() - self.last_activity


class SystemEvent(models.Model):
    """
    Track system-level events and errors
    """
    EVENT_TYPES = [
        ('ERROR', 'Error'),
        ('WARNING', 'Warning'),
        ('INFO', 'Information'),
        ('SECURITY', 'Security Event'),
        ('PERFORMANCE', 'Performance Issue'),
        ('BACKUP', 'Backup Event'),
        ('MAINTENANCE', 'Maintenance Event'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    title = models.CharField(max_length=255)
    description = models.TextField()
    details = models.JSONField(default=dict, encoder=DjangoJSONEncoder, blank=True)
    
    # Error tracking
    error_code = models.CharField(max_length=50, blank=True)
    stack_trace = models.TextField(blank=True)
    
    # Affected components
    component = models.CharField(max_length=100, blank=True)  # e.g., 'Project', 'User', 'System'
    severity = models.CharField(max_length=10, choices=[
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ], default='LOW')
    
    # Resolution
    is_resolved = models.BooleanField(default=False)
    resolved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['event_type', 'timestamp']),
            models.Index(fields=['severity', 'timestamp']),
            models.Index(fields=['is_resolved', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.event_type}: {self.title} at {self.timestamp}"


class ActivityDashboard(models.Model):
    """
    Store dashboard statistics and metrics for quick access
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date = models.DateField(unique=True)
    last_updated = models.DateTimeField(default=timezone.now)
    
    # Daily statistics
    total_activities = models.PositiveIntegerField(default=0)
    total_logins = models.PositiveIntegerField(default=0)
    total_project_changes = models.PositiveIntegerField(default=0)
    total_system_events = models.PositiveIntegerField(default=0)
    
    # User activity breakdown
    active_users = models.PositiveIntegerField(default=0)
    new_users = models.PositiveIntegerField(default=0)
    
    # Project activity breakdown
    projects_created = models.PositiveIntegerField(default=0)
    projects_updated = models.PositiveIntegerField(default=0)
    projects_approved = models.PositiveIntegerField(default=0)
    projects_rejected = models.PositiveIntegerField(default=0)
    
    # Error tracking
    errors_count = models.PositiveIntegerField(default=0)
    warnings_count = models.PositiveIntegerField(default=0)
    
    # Performance metrics
    avg_response_time = models.FloatField(default=0.0)  # in milliseconds
    peak_concurrent_users = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['-date']
    
    def __str__(self):
        return f"Dashboard for {self.date}"


class AuditTrail(models.Model):
    """
    Comprehensive audit trail for sensitive operations
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Operation details
    operation = models.CharField(max_length=50)  # e.g., 'USER_PERMISSION_CHANGE', 'PROJECT_DELETE'
    resource_type = models.CharField(max_length=50)  # e.g., 'User', 'Project', 'Funding'
    resource_id = models.CharField(max_length=50)
    
    # Before and after states
    before_state = models.JSONField(default=dict, encoder=DjangoJSONEncoder, blank=True)
    after_state = models.JSONField(default=dict, encoder=DjangoJSONEncoder, blank=True)
    
    # Context
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    session_id = models.CharField(max_length=40, blank=True)
    
    # Approval workflow
    requires_approval = models.BooleanField(default=False)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_audits')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['operation', 'timestamp']),
            models.Index(fields=['resource_type', 'resource_id']),
            models.Index(fields=['user', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.operation} on {self.resource_type}:{self.resource_id} by {self.user}"


class GallerySettings(models.Model):
    """
    Settings for project gallery configuration
    """
    # Gallery display settings
    max_images_per_page = models.PositiveIntegerField(
        default=12,
        verbose_name="حداکثر تعداد تصاویر در هر صفحه",
        help_text="تعداد تصاویری که در هر صفحه گالری نمایش داده می‌شود"
    )
    
    max_image_size_mb = models.PositiveIntegerField(
        default=5,
        verbose_name="حداکثر حجم تصویر (مگابایت)",
        help_text="حداکثر حجم مجاز برای هر تصویر در مگابایت"
    )
    
    thumbnail_size = models.PositiveIntegerField(
        default=200,
        verbose_name="اندازه تصاویر کوچک (پیکسل)",
        help_text="اندازه تصاویر کوچک در پیکسل"
    )
    
    # Gallery behavior settings
    enable_image_compression = models.BooleanField(
        default=True,
        verbose_name="فشرده‌سازی خودکار تصاویر",
        help_text="تصاویر به صورت خودکار فشرده می‌شوند"
    )
    
    allowed_image_formats = models.JSONField(
        default=list,
        verbose_name="فرمت‌های مجاز تصاویر",
        help_text="لیست فرمت‌های مجاز برای آپلود تصاویر"
    )
    
    # Gallery display options
    show_image_titles = models.BooleanField(
        default=True,
        verbose_name="نمایش عنوان تصاویر",
        help_text="عنوان تصاویر در گالری نمایش داده می‌شود"
    )
    
    show_image_descriptions = models.BooleanField(
        default=True,
        verbose_name="نمایش توضیحات تصاویر",
        help_text="توضیحات تصاویر در گالری نمایش داده می‌شود"
    )
    
    show_upload_dates = models.BooleanField(
        default=True,
        verbose_name="نمایش تاریخ آپلود",
        help_text="تاریخ آپلود تصاویر نمایش داده می‌شود"
    )
    
    # Gallery layout settings
    images_per_row = models.PositiveIntegerField(
        default=4,
        verbose_name="تعداد تصاویر در هر ردیف",
        help_text="تعداد تصاویری که در هر ردیف نمایش داده می‌شود"
    )
    
    enable_lightbox = models.BooleanField(
        default=True,
        verbose_name="فعال‌سازی نمایش بزرگ تصاویر",
        help_text="امکان نمایش تصاویر در اندازه بزرگ فعال است"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name="آخرین بروزرسانی توسط"
    )
    
    class Meta:
        verbose_name = "تنظیمات گالری"
        verbose_name_plural = "تنظیمات گالری"
    
    def __str__(self):
        return f"تنظیمات گالری - {self.max_images_per_page} تصویر در صفحه"
    
    def save(self, *args, **kwargs):
        # Set default allowed formats if not provided
        if not self.allowed_image_formats:
            self.allowed_image_formats = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
        super().save(*args, **kwargs)
    
    @classmethod
    def get_settings(cls):
        """Get the current gallery settings, create default if not exists"""
        settings_obj, created = cls.objects.get_or_create(
            id=1,
            defaults={
                'max_images_per_page': 12,
                'max_image_size_mb': 5,
                'thumbnail_size': 200,
                'enable_image_compression': True,
                'allowed_image_formats': ['image/jpeg', 'image/png', 'image/gif', 'image/webp'],
                'show_image_titles': True,
                'show_image_descriptions': True,
                'show_upload_dates': True,
                'images_per_row': 4,
                'enable_lightbox': True,
            }
        )
        return settings_obj
