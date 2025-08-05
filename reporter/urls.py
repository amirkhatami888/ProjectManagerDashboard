from django.urls import path
from . import views

app_name = 'reporter'

urlpatterns = [
    # Dashboard
    path('dashboard/', views.reporter_dashboard, name='reporter_dashboard'),
    
    # Project Reports
    path('projects/', views.ProjectReportListView.as_view(), name='project_reports'),
    path('projects/create/', views.ProjectReportCreateView.as_view(), name='create_project_report'),
    path('projects/<int:pk>/', views.ProjectReportDetailView.as_view(), name='project_report_detail'),
    path('projects/<int:pk>/edit/', views.ProjectReportUpdateView.as_view(), name='edit_project_report'),
    path('projects/<int:pk>/delete/', views.ProjectReportDeleteView.as_view(), name='delete_project_report'),
    
    # SubProject Reports
    path('subprojects/', views.SubProjectReportListView.as_view(), name='subproject_reports'),
    path('subprojects/create/', views.SubProjectReportCreateView.as_view(), name='create_subproject_report'),
    path('subprojects/<int:pk>/', views.SubProjectReportDetailView.as_view(), name='subproject_report_detail'),
    path('subprojects/<int:pk>/edit/', views.SubProjectReportUpdateView.as_view(), name='edit_subproject_report'),
    path('subprojects/<int:pk>/delete/', views.SubProjectReportDeleteView.as_view(), name='delete_subproject_report'),
    
    # Search and Reports
    path('search-history/', views.search_history_view, name='search_history'),
    path('program-search/', views.program_search_view, name='program_search'),
    path('create-report-from-search/', views.create_report_from_search, name='create_report_from_search'),
    path('my-searches/', views.user_search_history, name='user_search_history'),
    path('export-excel/', views.export_search_results_excel, name='export_excel'),
    path('export-program-excel/', views.export_program_search_results_excel, name='export_program_excel'),
    
    # Project Map View
    path('projects-map/', views.projects_map_view, name='projects_map'),
] 