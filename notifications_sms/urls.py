from django.urls import path
from . import views

urlpatterns = [
    # Dashboard views
    path('dashboard/', views.sms_dashboard, name='sms_dashboard'),
    path('expert/', views.expert_sms_dashboard, name='expert_sms_dashboard'),
    
    # Alert system
    path('alerts/', views.alerts_dashboard, name='alerts_dashboard'),
    path('alerts/send-outdated/', views.send_outdated_alerts, name='send_outdated_alerts'),
    path('alerts/send-unexamined/', views.send_unexamined_alerts, name='send_unexamined_alerts'),
    
    # Settings
    path('settings/', views.sms_settings, name='sms_settings'),
    path('settings/edit/', views.edit_sms_settings, name='edit_sms_settings'),
    path('settings/check-credit/', views.check_credit, name='check_credit'),
    path('settings/test-sms/', views.test_sms, name='test_sms'),
    
    # Provider management
    path('providers/edit/<int:provider_id>/', views.edit_sms_provider, name='edit_sms_provider'),
    path('providers/toggle/<int:provider_id>/', views.toggle_sms_provider, name='toggle_sms_provider'),
    
    # Templates
    path('templates/', views.manage_templates, name='manage_templates'),
    # path('templates/create/', views.create_template, name='create_template'),  # Disabled - users can only edit existing templates
    path('templates/edit/<int:template_id>/', views.edit_template, name='edit_template'),
    path('templates/quick-edit/', views.quick_edit_template, name='quick_edit_template'),
    path('templates/content/', views.get_template_content, name='get_template_content'),
    
    # Sending SMS
    path('send/', views.send_sms, name='send_sms'),
    path('send/bulk/', views.send_bulk_sms, name='send_bulk_sms'),
    
    # Logs
    path('logs/', views.sms_logs, name='sms_logs'),
] 