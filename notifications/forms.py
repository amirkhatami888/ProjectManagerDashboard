from django import forms
from .models import SMSSettings, RejectionSMSSettings, ExpertReminderSMSSettings
from accounts.models import User
from creator_project.models import Project

class SMSSettingsForm(forms.ModelForm):
    class Meta:
        model = SMSSettings
        fields = ['enabled', 'api_key', 'sender_number', 'inactivity_days', 'message_template']
        widgets = {
            'enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'api_key': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'sender_number': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'inactivity_days': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 365}),
            'message_template': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'متن پیام با {project_name} برای نام پروژه'}),
        }
        help_texts = {
            'api_key': 'کلید API دریافتی از سامانه پیامک',
            'sender_number': 'شماره فرستنده پیامک (اختیاری)',
            'inactivity_days': 'تعداد روزهایی که اگر پروژه بروزرسانی نشود، پیامک ارسال می‌شود',
            'message_template': 'از {project_name} برای نمایش نام پروژه استفاده کنید',
        }


class RejectionSMSSettingsForm(forms.ModelForm):
    class Meta:
        model = RejectionSMSSettings
        fields = ['enabled', 'message_template']
        widgets = {
            'enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'message_template': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'متن پیام با {rejection_reason} برای دلیل رد پروژه'}),
        }
        help_texts = {
            'message_template': 'از {rejection_reason} برای نمایش دلیل رد پروژه و {project_name} برای نام پروژه استفاده کنید',
        }


class ExpertReminderSMSSettingsForm(forms.ModelForm):
    class Meta:
        model = ExpertReminderSMSSettings
        fields = ['enabled', 'reminder_days', 'message_template']
        widgets = {
            'enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'reminder_days': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 30}),
            'message_template': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'متن پیام با {project_name} برای نام پروژه'}),
        }
        help_texts = {
            'reminder_days': 'تعداد روزهایی که اگر پروژه توسط کارشناس بررسی نشود، پیامک ارسال می‌شود',
            'message_template': 'از {project_name} برای نمایش نام پروژه استفاده کنید',
        }


class AnnouncementSMSForm(forms.Form):
    RECIPIENT_CHOICES = [
        ('all', 'همه کاربران'),
        ('province', 'کاربران یک استان'),
        ('role', 'کاربران با نقش خاص'),
    ]
    
    ROLE_CHOICES = [
        ('', '-- انتخاب نقش --'),
        ('PROVINCE_MANAGER', 'مدیر استان'),
        ('EXPERT', 'کارشناس'),
        ('VICE_CHIEF_EXECUTIVE', 'معاون اجرایی'),
        ('CHIEF_EXECUTIVE', 'مدیر اجرایی'),
        ('CEO', 'مدیرعامل'),
    ]
    
    recipient_type = forms.ChoiceField(
        choices=RECIPIENT_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='all',
        label='گیرندگان'
    )
    
    province = forms.ChoiceField(
        choices=[('', '-- انتخاب استان --')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select', 'disabled': 'disabled'}),
        label='استان'
    )
    
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select', 'disabled': 'disabled'}),
        label='نقش'
    )
    
    message = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        label='متن پیام'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Get provinces from Project model and add to choices
        provinces = Project.objects.values_list('province', flat=True).distinct().order_by('province')
        province_choices = [('', '-- انتخاب استان --')] + [(p, p) for p in provinces if p]
        self.fields['province'].choices = province_choices 