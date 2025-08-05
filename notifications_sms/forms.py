from django import forms
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.db.models import Q

from .models import SMSTemplate, SMSSettings, SMSProvider
from accounts.models import User

class SMSSettingsForm(forms.ModelForm):
    """Form for editing SMS settings"""
    class Meta:
        model = SMSSettings
        fields = [
            'provider', 'outdated_project_days', 'not_examined_days',
            'auto_send_outdated', 'auto_send_rejected', 'auto_send_not_examined', 
            'auto_send_funding_approved', 'check_interval_hours'
        ]
        widgets = {
            'outdated_project_days': forms.NumberInput(attrs={'min': 1, 'max': 365, 'class': 'form-control'}),
            'not_examined_days': forms.NumberInput(attrs={'min': 1, 'max': 30, 'class': 'form-control'}),
            'check_interval_hours': forms.NumberInput(attrs={'min': 1, 'max': 168, 'class': 'form-control'}),
            'provider': forms.Select(attrs={'class': 'form-control'}),
        }

class SMSProviderForm(forms.ModelForm):
    """Form for creating/editing SMS provider"""
    class Meta:
        model = SMSProvider
        fields = ['name', 'provider_type', 'base_url', 'api_key', 'sender_number', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'نام سرویس دهنده (مثال: IPPanel اصلی)'
            }),
            'provider_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'base_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://rest.ippanel.com/v1'
            }),
            'api_key': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'کلید API دریافتی از پنل IPPanel'
            }),
            'sender_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+985000404223'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

class SMSTemplateForm(forms.ModelForm):
    """Form for creating/editing SMS templates"""
    class Meta:
        model = SMSTemplate
        fields = ['name', 'type', 'content', 'is_default']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 5}),
        }

class SendSMSForm(forms.Form):
    """Form for sending individual SMS"""
    recipient = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True).order_by('username'),
        label=_('Recipient'),
        widget=forms.Select(attrs={'class': 'select2'}),
        empty_label="-- انتخاب کاربر --"
    )
    message = forms.CharField(
        label=_('Message'),
        widget=forms.Textarea(attrs={'rows': 5, 'maxlength': 1000}),
        max_length=1000,
        help_text=_('Maximum 1000 characters')
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Update recipient queryset to include more detailed display
        self.fields['recipient'].queryset = User.objects.filter(
            is_active=True
        ).select_related().order_by('username')
    
    def clean_recipient(self):
        """Validate that the recipient has a phone number"""
        recipient = self.cleaned_data.get('recipient')
        if recipient and not recipient.phone_number:
            raise forms.ValidationError(
                _('Selected user does not have a phone number. Please contact the administrator to add a phone number for this user.')
            )
        return recipient
    
    def clean_message(self):
        """Validate message content"""
        message = self.cleaned_data.get('message')
        if message:
            message = message.strip()
            if len(message) < 1:
                raise forms.ValidationError(_('Message cannot be empty.'))
            if len(message) > 1000:
                raise forms.ValidationError(_('Message cannot be longer than 1000 characters.'))
        return message

class BulkSMSForm(forms.Form):
    """Form for sending bulk SMS"""
    ROLE_CHOICES = (
        ('', '-- All Roles --'),
        ('ADMIN', _('Admin')),
        ('CEO', _('CEO')),
        ('CHIEF_EXECUTIVE', _('Chief Executive')),
        ('VICE_CHIEF_EXECUTIVE', _('Vice Chief Executive')),
        ('EXPERT', _('Expert')),
        ('PROVINCE_MANAGER', _('Province Manager')),
    )
    
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        label=_('User Role'),
        required=False
    )
    province = forms.ChoiceField(
        choices=[('', '-- All Provinces --')] + list(User.PROVINCE_CHOICES),
        label=_('Province'),
        required=False
    )
    message = forms.CharField(
        label=_('Message'),
        widget=forms.Textarea(attrs={'rows': 5})
    ) 