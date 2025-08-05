from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('sms-settings/', views.sms_settings, name='sms_settings'),
    path('rejection-sms-settings/', views.rejection_sms_settings, name='rejection_sms_settings'),
    path('expert-reminder-sms-settings/', views.expert_reminder_sms_settings, name='expert_reminder_sms_settings'),
    path('sms-logs/', views.sms_logs, name='sms_logs'),
    path('send-announcement/', views.send_announcement, name='send_announcement'),
    path('expert-send-sms/', views.expert_send_sms, name='expert_send_sms'),
] 