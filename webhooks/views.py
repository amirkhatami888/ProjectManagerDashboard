import json
import logging
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import WebhookEvent, WebhookConfiguration
from .utils import verify_github_signature, parse_github_event, process_webhook_event
from .forms import WebhookConfigurationForm

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def github_webhook(request):
    """
    Handle GitHub webhook events
    """
    try:
        # Get the raw payload
        payload_body = request.body
        
        # Get the signature header
        signature_header = request.META.get('HTTP_X_HUB_SIGNATURE_256', '')
        
        # Get the event type
        event_type = request.META.get('HTTP_X_GITHUB_EVENT', '')
        
        # Parse the JSON payload
        try:
            payload = json.loads(payload_body.decode('utf-8'))
        except json.JSONDecodeError:
            logger.error("Invalid JSON payload")
            return HttpResponse(status=400)
        
        # Find the webhook configuration for this repository
        repository_name = payload.get('repository', {}).get('full_name', '')
        config = WebhookConfiguration.objects.filter(
            repository_url__icontains=repository_name,
            is_active=True
        ).first()
        
        # Verify signature if secret token is configured
        if config and config.secret_token:
            if not verify_github_signature(payload_body, signature_header, config.secret_token):
                logger.warning(f"Invalid signature for repository {repository_name}")
                return HttpResponse(status=401)
        
        # Parse the event data
        event_data = parse_github_event(payload)
        
        # Process the webhook event
        success, message = process_webhook_event(event_data, payload)
        
        if success:
            logger.info(f"Webhook processed successfully: {message}")
            return HttpResponse(status=200)
        else:
            logger.error(f"Webhook processing failed: {message}")
            return HttpResponse(status=500)
    
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return HttpResponse(status=500)


@login_required
@user_passes_test(lambda u: u.is_staff)
def webhook_dashboard(request):
    """
    Dashboard for managing webhook events and configurations
    """
    # Get recent webhook events
    events = WebhookEvent.objects.all()[:50]
    
    # Get webhook configurations
    configurations = WebhookConfiguration.objects.all()
    
    # Statistics
    total_events = WebhookEvent.objects.count()
    successful_events = WebhookEvent.objects.filter(status='completed').count()
    failed_events = WebhookEvent.objects.filter(status='failed').count()
    pending_events = WebhookEvent.objects.filter(status='pending').count()
    
    context = {
        'events': events,
        'configurations': configurations,
        'total_events': total_events,
        'successful_events': successful_events,
        'failed_events': failed_events,
        'pending_events': pending_events,
    }
    
    return render(request, 'webhooks/dashboard.html', context)


@login_required
@user_passes_test(lambda u: u.is_staff)
def webhook_events(request):
    """
    List all webhook events with filtering and pagination
    """
    events = WebhookEvent.objects.all()
    
    # Filtering
    event_type = request.GET.get('event_type')
    status = request.GET.get('status')
    repository = request.GET.get('repository')
    
    if event_type:
        events = events.filter(event_type=event_type)
    if status:
        events = events.filter(status=status)
    if repository:
        events = events.filter(repository__icontains=repository)
    
    # Pagination
    paginator = Paginator(events, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'event_types': WebhookEvent.EVENT_TYPES,
        'status_choices': WebhookEvent.STATUS_CHOICES,
        'filters': {
            'event_type': event_type,
            'status': status,
            'repository': repository,
        }
    }
    
    return render(request, 'webhooks/events.html', context)


@login_required
@user_passes_test(lambda u: u.is_staff)
def webhook_event_detail(request, event_id):
    """
    Show details of a specific webhook event
    """
    event = get_object_or_404(WebhookEvent, id=event_id)
    
    context = {
        'event': event,
    }
    
    return render(request, 'webhooks/event_detail.html', context)


@login_required
@user_passes_test(lambda u: u.is_staff)
def webhook_configurations(request):
    """
    List and manage webhook configurations
    """
    configurations = WebhookConfiguration.objects.all()
    
    context = {
        'configurations': configurations,
    }
    
    return render(request, 'webhooks/configurations.html', context)


@login_required
@user_passes_test(lambda u: u.is_staff)
def webhook_configuration_create(request):
    """
    Create a new webhook configuration
    """
    if request.method == 'POST':
        form = WebhookConfigurationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Webhook configuration created successfully.')
            return redirect('webhooks:configurations')
    else:
        form = WebhookConfigurationForm()
    
    context = {
        'form': form,
        'title': 'Create Webhook Configuration',
    }
    
    return render(request, 'webhooks/configuration_form.html', context)


@login_required
@user_passes_test(lambda u: u.is_staff)
def webhook_configuration_edit(request, config_id):
    """
    Edit an existing webhook configuration
    """
    config = get_object_or_404(WebhookConfiguration, id=config_id)
    
    if request.method == 'POST':
        form = WebhookConfigurationForm(request.POST, instance=config)
        if form.is_valid():
            form.save()
            messages.success(request, 'Webhook configuration updated successfully.')
            return redirect('webhooks:configurations')
    else:
        form = WebhookConfigurationForm(instance=config)
    
    context = {
        'form': form,
        'config': config,
        'title': 'Edit Webhook Configuration',
    }
    
    return render(request, 'webhooks/configuration_form.html', context)


@login_required
@user_passes_test(lambda u: u.is_staff)
def webhook_configuration_delete(request, config_id):
    """
    Delete a webhook configuration
    """
    config = get_object_or_404(WebhookConfiguration, id=config_id)
    
    if request.method == 'POST':
        config.delete()
        messages.success(request, 'Webhook configuration deleted successfully.')
        return redirect('webhooks:configurations')
    
    context = {
        'config': config,
    }
    
    return render(request, 'webhooks/configuration_confirm_delete.html', context)


@login_required
@user_passes_test(lambda u: u.is_staff)
def webhook_test(request, config_id):
    """
    Test a webhook configuration
    """
    config = get_object_or_404(WebhookConfiguration, id=config_id)
    
    # This would typically send a test webhook to GitHub
    # For now, we'll just show a success message
    messages.info(request, f'Test webhook would be sent to {config.repository_url}')
    
    return redirect('webhooks:configurations')
