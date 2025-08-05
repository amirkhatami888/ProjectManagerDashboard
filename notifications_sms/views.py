from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from django.views.decorators.csrf import csrf_exempt
import json

from .models import SMSTemplate, SMSSettings, SMSLog, SMSProvider
from .utils import IPPanelSMSSender
from .forms import SMSTemplateForm, SMSSettingsForm, SendSMSForm, BulkSMSForm, SMSProviderForm
from accounts.models import User
from creator_project.models import Project
from creator_subproject.models import SubProject

def is_admin_or_chief(user):
    """Check if user is admin, CEO, or chief executive"""
    return user.is_admin or user.is_ceo or user.is_chief_executive

def is_expert(user):
    """Check if user is an expert"""
    return user.is_expert

def is_expert_for_sms(user):
    """Check if user is admin, CEO, chief executive or expert"""
    return is_admin_or_chief(user) or user.is_expert

@login_required
def sms_dashboard(request):
    """Dashboard for SMS management (admin/chief only)"""
    # Restrict access to province managers and experts
    if request.user.is_province_manager or request.user.is_expert:
        messages.error(request, "شما مجوز دسترسی به سامانه پیامک را ندارید.")
        return redirect('dashboard:dashboard')
    
    settings = SMSSettings.get_settings()
    providers = SMSProvider.objects.all()
    templates = SMSTemplate.objects.all().order_by('-is_default', 'type')
    recent_logs = SMSLog.objects.all()[:50]
    
    # Stats
    total_sent = SMSLog.objects.filter(status='SENT').count()
    total_failed = SMSLog.objects.filter(status='FAILED').count()
    
    context = {
        'settings': settings,
        'providers': providers,
        'templates': templates,
        'recent_logs': recent_logs,
        'total_sent': total_sent,
        'total_failed': total_failed,
    }
    
    return render(request, 'notifications_sms/dashboard.html', context)

@login_required
@user_passes_test(is_expert)
def expert_sms_dashboard(request):
    """Limited SMS dashboard for experts"""
    templates = SMSTemplate.objects.filter(created_by=request.user) | \
                SMSTemplate.objects.filter(is_default=True)
    
    recent_logs = SMSLog.objects.filter(sender=request.user)[:50]
    
    # Stats
    total_sent = SMSLog.objects.filter(sender=request.user, status='SENT').count()
    total_failed = SMSLog.objects.filter(sender=request.user, status='FAILED').count()
    
    context = {
        'templates': templates,
        'recent_logs': recent_logs,
        'total_sent': total_sent,
        'total_failed': total_failed,
        'can_send_sms': is_expert_for_sms(request.user)
    }
    
    return render(request, 'notifications_sms/expert_dashboard.html', context)

@login_required
def edit_sms_settings(request):
    """Edit SMS settings (admin/chief only)"""
    # Restrict access to province managers and experts
    if request.user.is_province_manager or request.user.is_expert:
        messages.error(request, "شما مجوز دسترسی به تنظیمات سامانه پیامک را ندارید.")
        return redirect('dashboard:dashboard')
    
    settings = SMSSettings.get_settings()
    providers = SMSProvider.objects.all()
    
    if request.method == 'POST':
        # Handle API key update directly
        api_key = request.POST.get('api_key', '').strip()
        
        if api_key:
            # Update the active provider's API key
            if settings.provider:
                settings.provider.api_key = api_key
                settings.provider.save()
                
                # Test the API key
                try:
                    from ippanel import Client
                    sms = Client(api_key)
                    credit = sms.get_credit()
                    messages.success(request, _(f'کلید API با موفقیت بروزرسانی شد. اعتبار باقی‌مانده: {credit}'))
                except Exception as e:
                    messages.warning(request, _(f'کلید API بروزرسانی شد اما تست اتصال ناموفق: {str(e)}'))
            else:
                messages.error(request, _('هیچ سرویس دهنده‌ای فعال نیست.'))
        
        # Handle other form fields
        form = SMSSettingsForm(request.POST, instance=settings)
        if form.is_valid():
            form.save()
            if not api_key:  # Only show this message if API key wasn't updated above
                messages.success(request, _('تنظیمات SMS با موفقیت بروزرسانی شد.'))
            return redirect('sms_dashboard')
    else:
        form = SMSSettingsForm(instance=settings)
    
    return render(request, 'notifications_sms/edit_settings.html', {
        'form': form,
        'providers': providers,
        'settings': settings
    })

@login_required
@user_passes_test(is_admin_or_chief)
def create_sms_provider(request):
    """Create a new IPPanel SMS provider"""
    # Check if IPPanel SDK is available
    try:
        from ippanel import Client
        ippanel_available = True
    except ImportError:
        ippanel_available = False
    
    if request.method == 'POST':
        action = request.POST.get('action', 'create')
        
        if action == 'test_connection':
            # Test API connection with provided credentials
            api_key = request.POST.get('api_key', '').strip()
            if not api_key:
                return JsonResponse({
                    "status": "ERROR",
                    "message": "کلید API الزامی است"
                })
            
            try:
                sms = Client(api_key)
                credit = sms.get_credit()
                return JsonResponse({
                    "status": "OK",
                    "message": "اتصال موفق",
                    "credit": credit
                })
            except Exception as e:
                return JsonResponse({
                    "status": "ERROR",
                    "message": f"خطا در اتصال: {str(e)}"
                })
        
        elif action == 'create':
            form = SMSProviderForm(request.POST)
            if form.is_valid():
                provider = form.save()
                
                # Test the provider if API key is provided
                if provider.api_key and ippanel_available:
                    try:
                        sms = Client(provider.api_key)
                        credit = sms.get_credit()
                        messages.success(request, _(f'سرویس دهنده پیامک ایجاد شد. اعتبار: {credit}'))
                    except Exception as e:
                        messages.warning(request, _(f'سرویس دهنده ایجاد شد ولی تست اتصال ناموفق: {str(e)}'))
                else:
                    messages.success(request, _('سرویس دهنده پیامک ایجاد شد.'))
                
                # If this is set as active, deactivate all others
                if provider.is_active:
                    SMSProvider.objects.exclude(pk=provider.pk).update(is_active=False)
                
                return redirect('sms_settings')
            else:
                return render(request, 'notifications_sms/create_provider.html', {
                    'form': form,
                    'ippanel_available': ippanel_available,
                    'title': _('ایجاد سرویس دهنده پیامک'),
                    'errors': form.errors
                })
    else:
        # Pre-fill form with IPPanel defaults
        initial_data = {
            'name': 'IPPanel',
            'provider_type': 'IPPANEL',
            'base_url': 'https://rest.ippanel.com/v1',
            'sender_number': '+985000404223',
            'is_active': True
        }
        form = SMSProviderForm(initial=initial_data)
    
    return render(request, 'notifications_sms/create_provider.html', {
        'form': form,
        'ippanel_available': ippanel_available,
        'title': _('ایجاد سرویس دهنده پیامک IPPanel')
    })

@login_required
@user_passes_test(is_admin_or_chief)
def edit_sms_provider(request, provider_id):
    """Edit an SMS provider"""
    provider = get_object_or_404(SMSProvider, id=provider_id)
    
    if request.method == 'POST':
        form = SMSProviderForm(request.POST, instance=provider)
        if form.is_valid():
            updated_provider = form.save()
            messages.success(request, _('SMS provider updated successfully.'))
            
            # If this is set as active, deactivate all others
            if updated_provider.is_active:
                SMSProvider.objects.exclude(pk=updated_provider.pk).update(is_active=False)
                
            return redirect('edit_sms_settings')
    else:
        form = SMSProviderForm(instance=provider)
    
    return render(request, 'notifications_sms/provider_form.html', {
        'form': form,
        'provider': provider,
        'title': _('Edit SMS Provider')
    })

@login_required
@user_passes_test(is_admin_or_chief)
def toggle_sms_provider(request, provider_id):
    """Toggle the active status of an SMS provider"""
    provider = get_object_or_404(SMSProvider, id=provider_id)
    
    # Toggle the active status
    provider.is_active = not provider.is_active
    provider.save()
    
    # If we're activating this provider, deactivate all others
    if provider.is_active:
        SMSProvider.objects.exclude(pk=provider.pk).update(is_active=False)
        messages.success(request, _(f'Provider "{provider.name}" has been activated.'))
    else:
        messages.success(request, _(f'Provider "{provider.name}" has been deactivated.'))
    
    return redirect('edit_sms_settings')

@login_required
@user_passes_test(is_expert_for_sms)
def manage_templates(request):
    """Manage SMS templates"""
    if is_admin_or_chief(request.user):
        templates = SMSTemplate.objects.all().order_by('-is_default', 'type')
    else:
        # Experts can see their own templates and all default templates
        templates = SMSTemplate.objects.filter(created_by=request.user) | \
                   SMSTemplate.objects.filter(is_default=True)
    
    context = {
        'templates': templates,
    }
    
    return render(request, 'notifications_sms/templates.html', context)

@login_required
@user_passes_test(is_expert_for_sms)
def create_template(request):
    """Create a new SMS template - DISABLED: Users can only edit existing templates"""
    messages.info(request, _('Creating new templates is disabled. You can only edit existing templates.'))
    return redirect('manage_templates')

@login_required
@user_passes_test(is_expert_for_sms)
def edit_template(request, template_id):
    """Edit an SMS template"""
    template = get_object_or_404(SMSTemplate, id=template_id)
    
    # Only allow editing if the user is admin/chief or is the creator
    if not is_admin_or_chief(request.user) and template.created_by != request.user:
        messages.error(request, _('You do not have permission to edit this template.'))
        return redirect('manage_templates')
    
    if request.method == 'POST':
        form = SMSTemplateForm(request.POST, instance=template)
        if form.is_valid():
            form.save()
            messages.success(request, _('Template updated successfully.'))
            return redirect('manage_templates')
    else:
        form = SMSTemplateForm(instance=template)
    
    return render(request, 'notifications_sms/template_form.html', {
        'form': form,
        'title': _('Edit Template'),
        'template': template
    })

@login_required
@user_passes_test(is_expert_for_sms)
def quick_edit_template(request):
    """Quick edit an SMS template via AJAX"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'})
    
    try:
        template_id = request.POST.get('template_id')
        template = get_object_or_404(SMSTemplate, id=template_id)
        
        # Only allow editing if the user is admin/chief or is the creator
        if not is_admin_or_chief(request.user) and template.created_by != request.user:
            return JsonResponse({'success': False, 'error': 'You do not have permission to edit this template.'})
        
        # Update template fields
        template.name = request.POST.get('name', template.name)
        template.content = request.POST.get('content', template.content)
        
        # Handle is_default checkbox
        is_default = request.POST.get('is_default') == 'on'
        if is_default and not template.is_default:
            # If setting as default, remove default from other templates of same type
            SMSTemplate.objects.filter(type=template.type, is_default=True).update(is_default=False)
        
        template.is_default = is_default
        template.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Template updated successfully'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@user_passes_test(is_expert_for_sms)
def get_template_content(request):
    """Get template content via AJAX"""
    if request.method != 'GET':
        return JsonResponse({'success': False, 'error': 'Method not allowed'})
    
    template_id = request.GET.get('template_id')
    if not template_id:
        return JsonResponse({'success': False, 'error': 'Template ID required'})
    
    try:
        template = get_object_or_404(SMSTemplate, id=template_id)
        
        # Check if user has access to this template
        if not is_admin_or_chief(request.user):
            # Experts can only access their own templates and default ones
            if template.created_by != request.user and not template.is_default:
                return JsonResponse({'success': False, 'error': 'Access denied'})
        
        return JsonResponse({
            'success': True,
            'content': template.content,
            'name': template.name,
            'type': template.get_type_display() if hasattr(template, 'get_type_display') else template.type
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@user_passes_test(is_expert_for_sms)
def send_sms(request):
    """Send an SMS to a user"""
    if request.method == 'POST':
        form = SendSMSForm(request.POST, user=request.user)
        if form.is_valid():
            recipient = form.cleaned_data['recipient']
            message = form.cleaned_data['message']
            
            if not recipient.phone_number:
                error_msg = _('Selected user does not have a phone number.')
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': str(error_msg)})
                messages.error(request, error_msg)
                return redirect('send_sms')
            
            # Validate message length
            if len(message) > 1000:
                error_msg = _('Message cannot be longer than 1000 characters.')
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': str(error_msg)})
                messages.error(request, error_msg)
                return redirect('send_sms')
            
            # Send the SMS
            try:
                print(f"Attempting to send SMS to {recipient.phone_number} from user {request.user}")
                print(f"Message: {message}")
                
                response = IPPanelSMSSender.send_sms(
                    recipient.phone_number,
                    message,
                    sender_user=request.user,
                    recipient_user=recipient,
                    template=None
                )
                
                print(f"SMS Response: {response}")
                
                if response.get('status') == 'OK':
                    success_msg = _('SMS sent successfully to {}.').format(recipient.get_full_name() or recipient.username)
                    print(f"Success message: {success_msg}")
                    
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': True, 
                            'message': str(success_msg),
                            'recipient': recipient.get_full_name() or recipient.username,
                            'phone': recipient.phone_number
                        })
                    messages.success(request, success_msg)
                    return redirect('sms_logs')
                else:
                    error_msg = _('Failed to send SMS: ') + str(response.get('message', 'Unknown error'))
                    # Add more detailed error information for debugging
                    if 'Expecting value' in str(response.get('message', '')):
                        error_msg += ' (This may be due to API configuration issues. Please check your IPPanel credentials.)'
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'success': False, 'error': str(error_msg)})
                    messages.error(request, error_msg)
                    return redirect('send_sms')
                    
            except Exception as e:
                error_msg = _('An error occurred while sending SMS: ') + str(e)
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': str(error_msg)})
                messages.error(request, error_msg)
                return redirect('send_sms')
        else:
            # Form validation errors
            errors = []
            for field, field_errors in form.errors.items():
                for error in field_errors:
                    errors.append(f"{form.fields.get(field, {}).get('label', field)}: {error}")
            
            error_msg = ' | '.join(errors) if errors else _('Please correct the form errors.')
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': str(error_msg)})
            messages.error(request, error_msg)
    else:
        form = SendSMSForm(user=request.user)
    
    return render(request, 'notifications_sms/send_sms.html', {'form': form})

@login_required
def send_bulk_sms(request):
    """Send SMS to multiple users (admin/chief only)"""
    # Restrict access to province managers and experts
    if request.user.is_province_manager or request.user.is_expert:
        messages.error(request, "شما مجوز دسترسی به ارسال پیامک گروهی را ندارید.")
        return redirect('dashboard:dashboard')
    
    if request.method == 'POST':
        form = BulkSMSForm(request.POST)
        if form.is_valid():
            role = form.cleaned_data.get('role')
            province = form.cleaned_data.get('province')
            message = form.cleaned_data['message']
            
            # Get users based on filters
            users = User.objects.filter(is_active=True)
            
            if role:
                users = users.filter(role=role)
            
            if province:
                users = users.filter(province=province)
            
            # Get phone numbers
            phone_numbers = [user.phone_number for user in users if user.phone_number]
            
            if not phone_numbers:
                messages.error(request, _('No users with phone numbers match the selected criteria.'))
                return redirect('send_bulk_sms')
            
            # Send bulk SMS
            results = IPPanelSMSSender.send_bulk_sms(
                phone_numbers,
                message,
                sender_user=request.user,
                template=None
            )
            
            messages.success(
                request, 
                _('Sent %(success)s SMS messages successfully. %(failed)s failed.') % {
                    'success': results['total_sent'],
                    'failed': results['total_failed']
                }
            )
            
            return redirect('sms_logs')
    else:
        form = BulkSMSForm()
    
    return render(request, 'notifications_sms/send_bulk_sms.html', {'form': form})

@login_required
def sms_logs(request):
    """View SMS logs"""
    # Restrict access to province managers and experts
    if request.user.is_province_manager or request.user.is_expert:
        messages.error(request, "شما مجوز دسترسی به گزارش‌های پیامک را ندارید.")
        return redirect('dashboard:dashboard')
    
    if is_admin_or_chief(request.user):
        logs = SMSLog.objects.all()
    else:
        # Experts can only see their own logs
        logs = SMSLog.objects.filter(sender=request.user)
    
    return render(request, 'notifications_sms/logs.html', {'logs': logs})

@login_required
def alerts_dashboard(request):
    """Dashboard for sending automated alert SMS messages"""
    # Restrict access to province managers and experts
    if request.user.is_province_manager or request.user.is_expert:
        messages.error(request, "شما مجوز دسترسی به داشبورد هشدارها را ندارید.")
        return redirect('dashboard:dashboard')
    
    settings = SMSSettings.get_settings()
    
    # Get counts for various alerts
    # 1. Outdated projects
    outdated_date = timezone.now() - timedelta(days=settings.outdated_project_days)
    outdated_projects_count = Project.objects.filter(
        updated_at__lt=outdated_date,
        status__in=['ONGOING', 'PLANNED']
    ).count()
    
    # 2. Unexamined projects
    delay_date = timezone.now() - timedelta(days=settings.not_examined_days)
    unexamined_count = SubProject.objects.filter(
        assigned_expert__isnull=False,
        last_expert_check__lt=delay_date
    ).count()
    
    # Get the templates
    outdated_template = SMSTemplate.objects.filter(
        type='PROJECT_OUTDATED', 
        is_default=True
    ).first()
    
    rejected_template = SMSTemplate.objects.filter(
        type='PROJECT_REJECTED', 
        is_default=True
    ).first()
    
    not_examined_template = SMSTemplate.objects.filter(
        type='PROJECT_NOT_EXAMINED', 
        is_default=True
    ).first()
    
    context = {
        'settings': settings,
        'outdated_projects_count': outdated_projects_count,
        'unexamined_count': unexamined_count,
        'outdated_template': outdated_template,
        'rejected_template': rejected_template,
        'not_examined_template': not_examined_template,
    }
    
    return render(request, 'notifications_sms/alerts_dashboard.html', context)

@login_required
@user_passes_test(is_admin_or_chief)
@require_POST
def send_outdated_alerts(request):
    """Send alerts for outdated projects"""
    settings = SMSSettings.get_settings()
    
    # Check if provider is configured
    if not settings.provider or not settings.provider.is_active:
        messages.error(request, _('No active SMS provider configured.'))
        return redirect('alerts_dashboard')
    
    # Use our command to send the alerts
    from django.core.management import call_command
    
    try:
        call_command('check_projects_and_send_sms')
        messages.success(request, _('Outdated project alerts sent successfully.'))
    except Exception as e:
        messages.error(request, _(f'Error sending alerts: {str(e)}'))
    
    return redirect('alerts_dashboard')

@login_required
@user_passes_test(is_admin_or_chief)
@require_POST
def send_unexamined_alerts(request):
    """Send alerts for unexamined projects"""
    settings = SMSSettings.get_settings()
    
    # Check if provider is configured
    if not settings.provider or not settings.provider.is_active:
        messages.error(request, _('No active SMS provider configured.'))
        return redirect('alerts_dashboard')
    
    # Use our command to send the alerts
    from django.core.management import call_command
    
    try:
        call_command('check_projects_and_send_sms')
        messages.success(request, _('Unexamined project alerts sent successfully.'))
    except Exception as e:
        messages.error(request, _(f'Error sending alerts: {str(e)}'))
    
    return redirect('alerts_dashboard')

@login_required
@user_passes_test(is_admin_or_chief)
def sms_settings(request):
    """IPPanel SMS Settings Configuration"""
    settings = SMSSettings.get_settings()
    providers = SMSProvider.objects.all()
    
    # Check if IPPanel SDK is available
    try:
        from ippanel import Client
        ippanel_available = True
    except ImportError:
        ippanel_available = False
    
    context = {
        'settings': settings,
        'providers': providers,
        'ippanel_available': ippanel_available,
        'current_provider': settings.provider if settings else None,
    }
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'update_settings':
            form = SMSSettingsForm(request.POST, instance=settings)
            if form.is_valid():
                form.save()
                messages.success(request, _('تنظیمات پیامک با موفقیت بروزرسانی شد.'))
                return redirect('sms_settings')
            else:
                context['form'] = form
                
        elif action == 'create_provider':
            provider_form = SMSProviderForm(request.POST)
            if provider_form.is_valid():
                provider = provider_form.save()
                messages.success(request, _('سرویس دهنده پیامک جدید ایجاد شد.'))
                
                # If this is set as active, deactivate all others
                if provider.is_active:
                    SMSProvider.objects.exclude(pk=provider.pk).update(is_active=False)
                    
                return redirect('sms_settings')
            else:
                context['provider_form'] = provider_form
                
        elif action == 'update_provider':
            # Handle simple API key update
            api_key = request.POST.get('api_key', '').strip()
            if api_key:
                # Get or create the default provider
                provider, created = SMSProvider.objects.get_or_create(
                    name='IPPanel',
                    defaults={
                        'provider_type': 'IPPANEL',
                        'base_url': 'https://rest.ippanel.com/v1',
                        'sender_number': '+985000404223',
                        'is_active': True
                    }
                )
                
                # Update API key
                provider.api_key = api_key
                provider.is_active = True
                provider.save()
                
                # Deactivate all other providers
                SMSProvider.objects.exclude(pk=provider.pk).update(is_active=False)
                
                # Test the API key
                try:
                    from ippanel import Client
                    sms = Client(api_key)
                    credit = sms.get_credit()
                    messages.success(request, _(f'کلید API با موفقیت بروزرسانی شد. اعتبار: {credit}'))
                except Exception as e:
                    messages.warning(request, _(f'کلید API ذخیره شد اما تست اتصال ناموفق: {str(e)}'))
                
                return redirect('sms_settings')
            else:
                messages.error(request, _('لطفاً کلید API را وارد کنید.'))
    
    # Initialize forms if not already set
    if 'form' not in context:
        context['form'] = SMSSettingsForm(instance=settings)
    if 'provider_form' not in context:
        context['provider_form'] = SMSProviderForm()
    
    return render(request, 'notifications_sms/sms_settings.html', context)

@login_required
@user_passes_test(is_admin_or_chief)
@csrf_exempt
def check_credit(request):
    """Check remaining credit from IPPanel"""
    if request.method == 'POST':
        try:
            result = IPPanelSMSSender.get_credit()
            return JsonResponse(result)
        except Exception as e:
            return JsonResponse({
                "status": "ERROR",
                "message": f"خطا در بررسی اعتبار: {str(e)}"
            })
    
    return JsonResponse({"status": "ERROR", "message": "Invalid request method"})

@login_required
@user_passes_test(is_admin_or_chief)
@csrf_exempt
def test_sms(request):
    """Send a test SMS to verify configuration"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            phone_number = data.get('phone_number', '').strip()
            test_message = data.get('message', 'این یک پیام تست از سیستم مدیریت پروژه است.')
            
            if not phone_number:
                return JsonResponse({
                    "status": "ERROR",
                    "message": "شماره تلفن الزامی است"
                })
            
            # Send test SMS
            result = IPPanelSMSSender.send_sms(
                phone_number,
                test_message,
                sender_user=request.user
            )
            
            if result["status"] == "OK":
                return JsonResponse({
                    "status": "OK",
                    "message": "پیام تست با موفقیت ارسال شد",
                    "message_id": result.get("message_id", "")
                })
            else:
                return JsonResponse({
                    "status": "ERROR",
                    "message": f"خطا در ارسال پیام: {result['message']}"
                })
                
        except json.JSONDecodeError:
            return JsonResponse({
                "status": "ERROR",
                "message": "داده‌های نامعتبر"
            })
        except Exception as e:
            return JsonResponse({
                "status": "ERROR",
                "message": f"خطای سیستم: {str(e)}"
            })
    
    return JsonResponse({"status": "ERROR", "message": "Invalid request method"})
