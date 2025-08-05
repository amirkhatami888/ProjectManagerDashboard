from django.db import models
from django.conf import settings

class SMSSettings(models.Model):
    """Settings for SMS notifications"""
    enabled = models.BooleanField(default=True, verbose_name="فعال")
    api_key = models.CharField(max_length=255, default="OWVlNWZlOWEtOTVhOC00YmM3LTliYWMtNTk0Y2Y1ZTg4MGI3NjU1NWNjMTgzMThmNWVkYmY3OWFjZWJjNzczNzI3N2I=", verbose_name="کلید API")
    sender_number = models.CharField(max_length=20, blank=True, null=True, verbose_name="شماره فرستنده")
    inactivity_days = models.PositiveIntegerField(default=30, verbose_name="حداکثر روزهای عدم بروزرسانی")
    message_template = models.TextField(default="با سلام وعرض ادب خدمت همکار گرامی لطفا به بروزسانی وضعیت پروژه {project_name} اقدام فرمایید", verbose_name="قالب پیام")
    last_run = models.DateTimeField(null=True, blank=True, verbose_name="آخرین اجرا")
    
    class Meta:
        verbose_name = "تنظیمات پیامک"
        verbose_name_plural = "تنظیمات پیامک"
    
    def __str__(self):
        return "تنظیمات پیامک"
    
    @classmethod
    def get_settings(cls):
        """Get or create settings"""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings


class RejectionSMSSettings(models.Model):
    """Settings for rejection SMS notifications"""
    enabled = models.BooleanField(default=True, verbose_name="فعال")
    message_template = models.TextField(default="با سلام وعرض ادب خدمت همکار گرامی به دلیل زیر پروژه نیازمند اصلاح است {rejection_reason}", verbose_name="قالب پیام")
    last_run = models.DateTimeField(null=True, blank=True, verbose_name="آخرین اجرا")
    
    class Meta:
        verbose_name = "تنظیمات پیامک رد پروژه"
        verbose_name_plural = "تنظیمات پیامک رد پروژه"
    
    def __str__(self):
        return "تنظیمات پیامک رد پروژه"
    
    @classmethod
    def get_settings(cls):
        """Get or create settings"""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings


class ExpertReminderSMSSettings(models.Model):
    """Settings for expert reminder SMS notifications"""
    enabled = models.BooleanField(default=True, verbose_name="فعال")
    reminder_days = models.PositiveIntegerField(default=3, verbose_name="روزهای تاخیر بررسی")
    message_template = models.TextField(default="با سلام وعرض ادب خدمت همکار گرامی لطفا به وضعیت پروژه {project_name} اقدام فرمایید", verbose_name="قالب پیام")
    last_run = models.DateTimeField(null=True, blank=True, verbose_name="آخرین اجرا")
    
    class Meta:
        verbose_name = "تنظیمات پیامک یادآوری کارشناس"
        verbose_name_plural = "تنظیمات پیامک یادآوری کارشناس"
    
    def __str__(self):
        return "تنظیمات پیامک یادآوری کارشناس"
    
    @classmethod
    def get_settings(cls):
        """Get or create settings"""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings


class SMSLog(models.Model):
    """Log of sent SMS messages"""
    STATUS_CHOICES = (
        ('pending', 'در انتظار'),
        ('sent', 'ارسال شده'),
        ('delivered', 'تحویل داده شده'),
        ('failed', 'خطا'),
    )
    
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sms_messages', verbose_name="دریافت کننده")
    message = models.TextField(verbose_name="متن پیام")
    project_name = models.CharField(max_length=255, verbose_name="نام پروژه")
    project_id = models.CharField(max_length=50, verbose_name="شناسه پروژه")
    province = models.CharField(max_length=50, verbose_name="استان")
    sent_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان ارسال")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="وضعیت")
    message_id = models.CharField(max_length=100, blank=True, null=True, verbose_name="شناسه پیام")
    error_message = models.TextField(blank=True, null=True, verbose_name="پیام خطا")
    
    class Meta:
        verbose_name = "گزارش پیامک"
        verbose_name_plural = "گزارش پیامک‌ها"
        ordering = ['-sent_at']
    
    def __str__(self):
        return f"پیامک به {self.recipient.username} - {self.sent_at}"


class ProjectExpertNotification(models.Model):
    """Model for tracking project notifications to experts"""
    NOTIFICATION_TYPE_CHOICES = (
        ('project_update', 'بروزرسانی پروژه'),
        ('project_rejection', 'رد پروژه'),
        ('expert_reminder', 'یادآوری کارشناس'),
    )
    
    project = models.ForeignKey('creator_project.Project', on_delete=models.CASCADE, related_name='expert_notifications', verbose_name="پروژه")
    expert = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='project_notifications', verbose_name="کارشناس")
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPE_CHOICES, default='project_update', verbose_name="نوع اطلاع‌رسانی")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان ایجاد")
    is_read = models.BooleanField(default=False, verbose_name="خوانده شده")
    notified_via_sms = models.BooleanField(default=False, verbose_name="اطلاع‌رسانی پیامکی")
    rejection_reason = models.TextField(blank=True, null=True, verbose_name="دلیل رد")
    
    class Meta:
        verbose_name = "اطلاع‌رسانی پروژه"
        verbose_name_plural = "اطلاع‌رسانی‌های پروژه"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_notification_type_display()} - {self.project.name} - {self.expert.username}"
