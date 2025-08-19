from django.urls import path
from . import views

app_name = 'activity_monitor'

urlpatterns = [
    # Dashboard and overview
    path('', views.activity_dashboard, name='dashboard'),
    path('analytics/', views.analytics, name='analytics'),
    
    # Activity logs
    path('logs/', views.activity_logs, name='activity_logs'),
    path('logs/<uuid:pk>/', views.ActivityLogDetailView.as_view(), name='activity_log_detail'),
    
    # User activity report
    path('user-activity-report/', views.user_activity_report, name='user_activity_report'),
    
    # Project changes
    path('project-changes/', views.project_changes, name='project_changes'),
    
    # Program changes
    path('program-changes/', views.program_changes, name='program_changes'),
    
    # Subproject changes
    path('subproject-changes/', views.subproject_changes, name='subproject_changes'),
    
    # System events
    path('system-events/', views.system_events, name='system_events'),
    path('system-events/<uuid:pk>/', views.SystemEventDetailView.as_view(), name='system_event_detail'),
    path('system-events/<uuid:event_id>/resolve/', views.resolve_system_event, name='resolve_system_event'),
    
    # User sessions
    path('sessions/', views.user_sessions, name='user_sessions'),
    
    # Audit trail
    path('audit-trail/', views.audit_trail, name='audit_trail'),
    path('audit-trail/<uuid:pk>/', views.AuditTrailDetailView.as_view(), name='audit_trail_detail'),
    path('audit-trail/<uuid:audit_id>/approve/', views.approve_audit_trail, name='approve_audit_trail'),
    
    # API endpoints
    path('api/summary/', views.api_activity_summary, name='api_summary'),
    path('api/recent-activities/', views.api_recent_activities, name='api_recent_activities'),
]
