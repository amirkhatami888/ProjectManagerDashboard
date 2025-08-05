from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()

class SMSProvider(models.Model):
    """SMS provider configuration"""
    name = models.CharField(_('Provider Name'), max_length=100)
    # base_url = models.URLField(_('API Base URL'), default='https://rest.ippanel.com/v1')
    base_url = models.URLField(_('API Base URL'), default='https://api2.ippanel.com/api/v1')

    username = models.CharField(_('Username'), max_length=100, blank=True, null=True)
    password = models.CharField(_('Password'), max_length=255, blank=True, null=True)
    api_key = models.CharField(_('API Key'), max_length=500)
    sender_number = models.CharField(_('Sender Number'), max_length=20, blank=True, null=True)
    is_active = models.BooleanField(_('Active'), default=False)
    
    # IPPanel specific fields
    provider_type = models.CharField(
        _('Provider Type'), 
        max_length=50, 
        choices=[
            ('IPPANEL', 'IPPanel'),
            ('FARAZSMS', 'FarazSMS'),
            ('CUSTOM', 'Custom')
        ],
        default='IPPANEL'
    )
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = _('SMS Provider')
        verbose_name_plural = _('SMS Providers')

class SMSSettings(models.Model):
    """Global SMS settings"""
    provider = models.ForeignKey(
        SMSProvider, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name=_('SMS Provider')
    )
    outdated_project_days = models.PositiveIntegerField(
        _('Days Until Project Considered Outdated'),
        default=30, 
        help_text=_('Number of days after which a project is considered outdated if not updated')
    )
    not_examined_days = models.PositiveIntegerField(
        _('Days Until Expert Reminder'),
        default=3,
        help_text=_('Number of days after which to remind experts about unexamined projects')
    )
    
    # Automation settings
    auto_send_outdated = models.BooleanField(
        _('Auto Send Outdated Project Notifications'),
        default=True,
        help_text=_('Automatically send SMS for outdated projects')
    )
    auto_send_rejected = models.BooleanField(
        _('Auto Send Rejected Project Notifications'),
        default=True,
        help_text=_('Automatically send SMS for rejected projects')
    )
    auto_send_not_examined = models.BooleanField(
        _('Auto Send Not Examined Project Notifications'),
        default=True,
        help_text=_('Automatically send SMS for not examined projects')
    )
    auto_send_funding_approved = models.BooleanField(
        _('Auto Send Funding Approved Notifications'),
        default=True,
        help_text=_('Automatically send SMS for approved funding requests')
    )
    
    # Time intervals in hours
    check_interval_hours = models.PositiveIntegerField(
        _('Check Interval (Hours)'),
        default=24,
        help_text=_('How often to check for outdated/unexamined projects (in hours)')
    )
    
    class Meta:
        verbose_name = _('SMS Settings')
        verbose_name_plural = _('SMS Settings')
    
    @classmethod
    def get_settings(cls):
        """Get or create settings singleton"""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings

class SMSTemplate(models.Model):
    """Templates for SMS messages"""
    PROJECT_OUTDATED = 'PROJECT_OUTDATED'
    PROJECT_REJECTED = 'PROJECT_REJECTED'
    PROJECT_NOT_EXAMINED = 'PROJECT_NOT_EXAMINED'
    FUNDING_REQUEST_APPROVED = 'FUNDING_REQUEST_APPROVED'
    CUSTOM = 'CUSTOM'
    
    TEMPLATE_TYPES = (
        (PROJECT_OUTDATED, _('Project Not Updated')),
        (PROJECT_REJECTED, _('Project Rejected')),
        (PROJECT_NOT_EXAMINED, _('Project Not Examined')),
        (FUNDING_REQUEST_APPROVED, _('Funding Request Approved')),
        (CUSTOM, _('Custom Message')),
    )
    
    name = models.CharField(_('Template Name'), max_length=100)
    type = models.CharField(_('Template Type'), max_length=50, choices=TEMPLATE_TYPES)
    content = models.TextField(_('Message Content'))
    is_default = models.BooleanField(_('Default Template'), default=False)
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='sms_templates',
        verbose_name=_('Created By')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        """Ensure only one default template per type"""
        if self.is_default:
            # Set all other templates of the same type to not default
            SMSTemplate.objects.filter(
                type=self.type, 
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = _('SMS Template')
        verbose_name_plural = _('SMS Templates')

class SMSLog(models.Model):
    """Log of sent SMS messages"""
    SENT = 'SENT'
    FAILED = 'FAILED'
    PENDING = 'PENDING'
    
    STATUS_CHOICES = (
        (SENT, _('Sent')),
        (FAILED, _('Failed')),
        (PENDING, _('Pending')),
    )
    
    sender = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='sent_sms',
        verbose_name=_('Sender')
    )
    recipient_user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='received_sms',
        verbose_name=_('Recipient User')
    )
    recipient_number = models.CharField(_('Recipient Number'), max_length=20)
    message = models.TextField(_('Message Content'))
    template = models.ForeignKey(
        SMSTemplate, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name=_('Template Used')
    )
    status = models.CharField(_('Status'), max_length=20, choices=STATUS_CHOICES, default=PENDING)
    error_message = models.TextField(_('Error Message'), blank=True, null=True)
    message_id = models.CharField(_('Message ID'), max_length=100, blank=True, null=True)
    provider = models.ForeignKey(
        SMSProvider, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name=_('Provider Used')
    )
    sent_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.recipient_number} - {self.sent_at}"
    
    class Meta:
        verbose_name = _('SMS Log')
        verbose_name_plural = _('SMS Logs')
        ordering = ['-sent_at']
