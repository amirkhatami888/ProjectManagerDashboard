from django.urls import path
from . import views

app_name = 'webhooks'

urlpatterns = [
    # GitHub webhook endpoint (no authentication required)
    path('github/', views.github_webhook, name='github_webhook'),
    
    # Dashboard and management views (staff only)
    path('dashboard/', views.webhook_dashboard, name='dashboard'),
    path('events/', views.webhook_events, name='events'),
    path('events/<int:event_id>/', views.webhook_event_detail, name='event_detail'),
    path('configurations/', views.webhook_configurations, name='configurations'),
    path('configurations/create/', views.webhook_configuration_create, name='configuration_create'),
    path('configurations/<int:config_id>/edit/', views.webhook_configuration_edit, name='configuration_edit'),
    path('configurations/<int:config_id>/delete/', views.webhook_configuration_delete, name='configuration_delete'),
    path('configurations/<int:config_id>/test/', views.webhook_test, name='configuration_test'),
] 