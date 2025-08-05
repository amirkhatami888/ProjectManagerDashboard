from django.urls import path
from . import views

urlpatterns = [
    path('project/<int:project_id>/', views.review_project, name='review_project'),
    path('subproject/<int:subproject_id>/', views.review_subproject, name='review_subproject'),
] 