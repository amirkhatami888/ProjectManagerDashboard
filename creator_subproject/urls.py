from django.urls import path
from . import views

app_name = 'creator_subproject'

urlpatterns = [
    # Subproject views
    path('subproject/list/', views.subproject_list, name='subproject_list'),
    path('subproject/list/<int:project_id>/', views.subproject_list, name='subproject_list_by_project'),
    path('subproject/<int:pk>/', views.subproject_detail, name='subproject_detail'),
    path('subproject/create/<int:project_id>/', views.subproject_create, name='subproject_create'),
    path('subproject/update/<int:subproject_id>/', views.subproject_update, name='subproject_update'),
    path('subproject/delete/<int:pk>/', views.subproject_delete, name='delete_subproject'),
    path('subproject/<int:pk>/add_situation_report/', views.subproject_add_situation_report, name='subproject_add_situation_report'),
    
    # Financial documents URLs
    path('subproject/<int:subproject_id>/financial-documents/', views.financial_documents, name='financial_documents'),
    path('subproject/<int:subproject_id>/financial-document/add/', views.add_financial_document, name='add_financial_document'),
    path('financial-document/<int:document_id>/edit/', views.edit_financial_document, name='edit_financial_document'),
    path('financial-document/<int:document_id>/delete/', views.delete_financial_document, name='delete_financial_document'),
    path('document-file/delete/<int:pk>/', views.delete_document_file, name='delete_document_file'),
    path('document-file/serve/<int:pk>/', views.serve_document_file, name='serve_document_file'), # New URL
    
    # Backward compatibility URLs for allocations
    path('subproject/<int:subproject_id>/allocations/', views.financial_documents, name='allocations'),
    path('subproject/<int:subproject_id>/allocation/add/', views.add_financial_document, name='add_allocation'),
    path('allocation/edit/<int:pk>/', views.edit_financial_document, name='edit_allocation'),
    path('allocation/delete/<int:pk>/', views.delete_financial_document, name='delete_allocation'),
    
    # Payments URLs
    path('subproject/<int:subproject_id>/payments/', views.payments, name='payments'),
    path('subproject/<int:subproject_id>/payment/add/', views.add_payment, name='add_payment'),
    path('payment/<int:payment_id>/edit/', views.edit_payment, name='edit_payment'),
    path('payment/<int:payment_id>/delete/', views.delete_payment, name='delete_payment'),
    
    # Financial Ledger URL
    path('subproject/<int:subproject_id>/financial-ledger/', views.financial_ledger, name='financial_ledger'),
    
    # Backward compatibility URLs for adjustment_allocations
    path('subproject/<int:subproject_id>/adjustment-allocations/', views.payments, name='adjustment_allocations'),
    path('subproject/<int:subproject_id>/adjustment-allocation/add/', views.add_payment, name='add_adjustment_allocation'),
    
    # Gallery related URLs
    path('subproject/<int:pk>/gallery/', views.subproject_gallery, name='subproject_gallery'),
    path('subproject/<int:subproject_id>/gallery/upload/', views.upload_gallery_image, name='upload_gallery_image'),
    path('gallery/image/<int:image_id>/delete/', views.delete_gallery_image, name='delete_gallery_image'),
    
    # Project situation URLs
    path('project/<int:project_id>/situations/', views.project_situations_list, name='project_situations_list'),
    path('project/<int:project_id>/situation/create/', views.project_situation_create, name='project_situation_create'),
    path('situation/<int:pk>/update/', views.project_situation_update, name='project_situation_update'),
    path('situation/<int:pk>/delete/', views.project_situation_delete, name='project_situation_delete'),
    path('situation/<int:pk>/toggle-resolved/', views.project_situation_toggle_resolved, name='project_situation_toggle_resolved'),
    
    # API endpoints
    path('api/subproject/<int:subproject_id>/dates/', views.get_subproject_dates, name='get_subproject_dates'),
    path('api/project/<int:project_id>/gantt-data/', views.get_project_gantt_data, name='get_project_gantt_data'),
] 