from django.urls import path, include
from . import views

app_name = 'creator_project'

urlpatterns = [
    # Project list view
    path('', views.project_list, name='project_list'),
    
    # Expert all projects view
    path('expert-all-projects/', views.expert_all_projects, name='expert_all_projects'),
    
    # Expert all programs view
    path('expert-all-programs/', views.expert_all_programs, name='expert_all_programs'),
    
    # Project create, update, delete
    path('create/', views.project_create, name='project_create'),
    path('<int:pk>/', views.project_detail, name='project_detail'),
    path('<int:pk>/update/', views.project_update, name='project_update'),
    path('<int:pk>/delete/', views.project_delete, name='project_delete'),
    
    # Project submission and approval
    path('<int:pk>/submit/', views.project_submit, name='project_submit'),
    path('<int:pk>/approve/', views.project_approve, name='project_approve'),
    path('<int:pk>/reject/', views.project_reject, name='project_reject'),
    
    # Project financials
    path('<int:pk>/financials/', views.project_financials, name='project_financials'),
    
    # Funding Request URLs
    path('funding-requests/', views.FundingRequestListView.as_view(), name='funding_request_list'),
    path('funding-requests/create/', views.FundingRequestCreateView.as_view(), name='funding_request_create'),
    path('funding-requests/<int:pk>/', views.FundingRequestDetailView.as_view(), name='funding_request_detail'),
    path('funding-requests/<int:pk>/update/', views.FundingRequestUpdateView.as_view(), name='funding_request_update'),
    path('funding-requests/<int:pk>/submit/', views.SubmitToExpertView.as_view(), name='funding_request_submit'),
    path('funding-requests/<int:pk>/expert-review/', views.ExpertReviewView.as_view(), name='expert_review'),
    path('funding-requests/<int:pk>/chief-review/', views.ChiefReviewView.as_view(), name='chief_review'),
    path('funding-requests/province/', views.ProvinceFundingRequestView.as_view(), name='province_funding_request'),
    
    # Funding Table and History URLs
    path('funding-table/', views.FundingTableView.as_view(), name='funding_table'),
    path('funding-history/', views.FundingHistoryView.as_view(), name='funding_history'),
    path('archive-funding-requests/', views.ArchiveFundingRequestsView.as_view(), name='archive_funding_requests'),
    path('export-funding-table/', views.ExportFundingTableView.as_view(), name='export_funding_table'),
    
    # Allocation list, edit, and delete URLs
    path('projects/<int:project_id>/allocations/', views.allocation_list, name='allocation_list'),
    path('projects/<int:pk>/allocations/add/', views.project_add_allocation, name='project_add_allocation'),
    path('allocations/<int:allocation_id>/edit/', views.allocation_edit, name='allocation_edit'),
    path('allocations/<int:allocation_id>/delete/', views.allocation_delete, name='allocation_delete'),
    
    # Subproject list and delete URLs
    path('projects/<int:project_id>/subprojects/', views.subproject_list, name='subproject_list'),
    path('subprojects/<int:subproject_id>/delete/', views.subproject_delete, name='subproject_delete'),
    
    # AJAX views
    path('get-program-details/', views.get_program_details, name='get_program_details'),
] 