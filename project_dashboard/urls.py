"""
URL configuration for project_dashboard project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('', RedirectView.as_view(url='/accounts/login/', permanent=True), name='home'),
    path('user/login/', RedirectView.as_view(url='/accounts/login/', permanent=True), name='old_login'),
    path('debug/', views.debug_info, name='debug_info'),
    path('dashboard/', include('dashboard.urls', namespace='dashboard')),
    path('programs/', include('creator_program.urls', namespace='creator_program')),
    path('projects/', include('creator_project.urls', namespace='creator_project')),
    path('subprojects/', include('creator_subproject.urls')),
    path('reviews/', include('creator_review.urls')),
    path('reporter/', include('reporter.urls')),
    path("notifications/", include("notifications.urls")),
    path("sms/", include("notifications_sms.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
