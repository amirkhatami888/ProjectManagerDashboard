from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.db.models import Q

from .models import SMSSettings, RejectionSMSSettings, ExpertReminderSMSSettings, SMSLog
from .forms import SMSSettingsForm, RejectionSMSSettingsForm, ExpertReminderSMSSettingsForm, AnnouncementSMSForm
from accounts.models import User
from utils.ippanel import IPPanelClient

def is_chief_user(user):
    """Check if user is a chief-level user"""
    return user.is_authenticated and (user.is_admin or user.is_ceo or user.is_chief_executive)

def is_expert_user(user):
    """Check if user is an expert"""
    return user.is_authenticated and user.is_expert

@login_required
@user_passes_test(is_chief_user)
def sms_settings(request):
    """View for managing SMS settings"""
    settings = SMSSettings.get_settings()
    
    if request.method == 'POST':
        form = SMSSettingsForm(request.POST, instance=settings)
        if form.is_valid():
            form.save()
            messages.success(request, 'تنظیمات پیامک با موفقیت ذخیره شد.')
            return redirect('notifications:sms_settings')
    else:
        form = SMSSettingsForm(instance=settings)
    
    context = {
        'form': form,
        'title': 'تنظیمات پیامک',
    }
    return render(request, 'notifications/sms_settings.html', context)

@login_required
@user_passes_test(is_chief_user)
def rejection_sms_settings(request):
    """View for managing rejection SMS settings"""
    settings = RejectionSMSSettings.get_settings()
    
    if request.method == 'POST':
        form = RejectionSMSSettingsForm(request.POST, instance=settings)
        if form.is_valid():
            form.save()
            messages.success(request, 'تنظیمات پیامک رد پروژه با موفقیت ذخیره شد.')
            return redirect('notifications:rejection_sms_settings')
    else:
        form = RejectionSMSSettingsForm(instance=settings)
    
    context = {
        'form': form,
        'title': 'تنظیمات پیامک رد پروژه',
    }
    return render(request, 'notifications/rejection_sms_settings.html', context)

@login_required
@user_passes_test(is_chief_user)
def expert_reminder_sms_settings(request):
    """View for managing expert reminder SMS settings"""
    settings = ExpertReminderSMSSettings.get_settings()
    
    if request.method == 'POST':
        form = ExpertReminderSMSSettingsForm(request.POST, instance=settings)
        if form.is_valid():
            form.save()
            messages.success(request, 'تنظیمات پیامک یادآوری کارشناس با موفقیت ذخیره شد.')
            return redirect('notifications:expert_reminder_sms_settings')
    else:
        form = ExpertReminderSMSSettingsForm(instance=settings)
    
    context = {
        'form': form,
        'title': 'تنظیمات پیامک یادآوری کارشناس',
    }
    return render(request, 'notifications/expert_reminder_sms_settings.html', context)

@login_required
@user_passes_test(is_chief_user)
def sms_logs(request):
    """View for SMS log history"""
    logs = SMSLog.objects.all()
    
    # Apply filters if any
    province = request.GET.get('province')
    status = request.GET.get('status')
    
    if province:
        logs = logs.filter(province=province)
    
    if status:
        logs = logs.filter(status=status)
    
    context = {
        'logs': logs,
        'title': 'گزارش پیامک‌ها',
        'province': province,
        'status': status,
    }
    return render(request, 'notifications/sms_logs.html', context)

@login_required
@user_passes_test(is_chief_user)
def send_announcement(request):
    """View for sending SMS announcements to users"""
    sms_settings = SMSSettings.get_settings()
    
    if request.method == 'POST':
        form = AnnouncementSMSForm(request.POST)
        if form.is_valid():
            recipient_type = form.cleaned_data['recipient_type']
            province = form.cleaned_data.get('province')
            role = form.cleaned_data.get('role')
            message_text = form.cleaned_data['message']
            
            # Get recipients based on selection
            recipients_query = User.objects.filter(is_active=True)
            
            if recipient_type == 'province' and province:
                recipients_query = recipients_query.filter(province=province)
            elif recipient_type == 'role' and role:
                recipients_query = recipients_query.filter(role=role)
            
            # Get recipients with phone numbers
            recipients = recipients_query.exclude(phone_number__isnull=True).exclude(phone_number='')
            
            if not recipients.exists():
                messages.warning(request, 'هیچ گیرنده‌ای با شماره تلفن یافت نشد.')
                return redirect('notifications:send_announcement')
            
            # Initialize SMS client
            sms_client = IPPanelClient(api_key=sms_settings.api_key)
            
            success_count = 0
            failed_count = 0
            
            # Send SMS to each recipient
            for user in recipients:
                try:
                    with transaction.atomic():
                        # Create log entry
                        sms_log = SMSLog.objects.create(
                            recipient=user,
                            message=message_text,
                            project_name="اطلاع‌رسانی عمومی",
                            project_id="ANNOUNCE",
                            province=user.province or "-",
                            status='pending'
                        )
                        
                        # Send SMS
                        result = sms_client.send_sms(
                            recipient_numbers=user.phone_number,
                            message_text=message_text,
                            sender_number=sms_settings.sender_number
                        )
                        
                        if result.get('meta', {}).get('status') == True:
                            # Update log with success
                            message_id = result.get('data', {}).get('message_id')
                            sms_log.status = 'sent'
                            sms_log.message_id = message_id
                            sms_log.save()
                            success_count += 1
                        else:
                            # Update log with error
                            error_message = result.get('meta', {}).get('message', 'Unknown error')
                            sms_log.status = 'failed'
                            sms_log.error_message = error_message
                            sms_log.save()
                            failed_count += 1
                            
                except Exception as e:
                    failed_count += 1
            
            messages.success(
                request, 
                f'پیامک به {success_count} کاربر با موفقیت ارسال شد. {failed_count} مورد ناموفق.'
            )
            return redirect('notifications:sms_logs')
    else:
        form = AnnouncementSMSForm()
    
    context = {
        'form': form,
        'title': 'ارسال پیامک عمومی',
    }
    return render(request, 'notifications/send_announcement.html', context)

@login_required
@user_passes_test(is_expert_user)
def expert_send_sms(request):
    """View for experts to send SMS to province users"""
    sms_settings = SMSSettings.get_settings()
    
    if request.method == 'POST':
        province = request.POST.get('province')
        message_text = request.POST.get('message')
        
        if not province or not message_text:
            messages.error(request, 'لطفا تمام فیلدها را پر کنید.')
            return redirect('notifications:expert_send_sms')
        
        # Get province users assigned to this expert
        expert_provinces = request.user.expert_provinces.values_list('province', flat=True)
        
        if province not in expert_provinces:
            messages.error(request, 'شما به این استان دسترسی ندارید.')
            return redirect('notifications:expert_send_sms')
        
        # Get province managers with phone numbers
        recipients = User.objects.filter(
            is_active=True,
            province=province,
            role='PROVINCE_MANAGER'
        ).exclude(phone_number__isnull=True).exclude(phone_number='')
        
        if not recipients.exists():
            messages.warning(request, 'هیچ مدیر استانی با شماره تلفن یافت نشد.')
            return redirect('notifications:expert_send_sms')
        
        # Initialize SMS client
        sms_client = IPPanelClient(api_key=sms_settings.api_key)
        
        success_count = 0
        failed_count = 0
        
        # Send SMS to each recipient
        for user in recipients:
            try:
                with transaction.atomic():
                    # Create log entry
                    sms_log = SMSLog.objects.create(
                        recipient=user,
                        message=message_text,
                        project_name="اطلاع‌رسانی کارشناس",
                        project_id="EXPERT",
                        province=province,
                        status='pending'
                    )
                    
                    # Send SMS
                    result = sms_client.send_sms(
                        recipient_numbers=user.phone_number,
                        message_text=message_text,
                        sender_number=sms_settings.sender_number
                    )
                    
                    if result.get('meta', {}).get('status') == True:
                        # Update log with success
                        message_id = result.get('data', {}).get('message_id')
                        sms_log.status = 'sent'
                        sms_log.message_id = message_id
                        sms_log.save()
                        success_count += 1
                    else:
                        # Update log with error
                        error_message = result.get('meta', {}).get('message', 'Unknown error')
                        sms_log.status = 'failed'
                        sms_log.error_message = error_message
                        sms_log.save()
                        failed_count += 1
                        
            except Exception as e:
                failed_count += 1
        
        messages.success(
            request, 
            f'پیامک به {success_count} مدیر استان با موفقیت ارسال شد. {failed_count} مورد ناموفق.'
        )
        return redirect('notifications:sms_logs')
    
    # Get provinces assigned to this expert
    expert_provinces = request.user.expert_provinces.values_list('province', flat=True)
    
    context = {
        'provinces': expert_provinces,
        'title': 'ارسال پیامک به مدیران استان',
    }
    return render(request, 'notifications/expert_send_sms.html', context)
