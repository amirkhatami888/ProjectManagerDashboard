from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_redirect, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Admin dashboard
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    
    # CEO dashboard
    path('dashboard/ceo/', views.ceo_dashboard, name='ceo_dashboard'),
    
    # Chief Executive dashboard
    path('dashboard/chief/', views.chief_executive_dashboard, name='chief_executive_dashboard'),
    
    # Vice Chief Executive dashboard
    path('dashboard/vice-chief/', views.vice_chief_executive_dashboard, name='vice_chief_executive_dashboard'),
    
    # Expert dashboard
    path('dashboard/expert/', views.expert_dashboard, name='expert_dashboard'),
    
    # Province Manager dashboard
    path('dashboard/province-manager/', views.province_manager_dashboard, name='province_manager_dashboard'),
] 