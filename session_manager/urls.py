from django.urls import path
from . import views

app_name = 'session_manager'

urlpatterns = [
    path('info/', views.session_info, name='session_info'),
    path('active/', views.active_sessions, name='active_sessions'),
    path('terminate/', views.terminate_session, name='terminate_session'),
]