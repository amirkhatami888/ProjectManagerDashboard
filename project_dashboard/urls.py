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
from django.urls import path, re_path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve as static_serve
from django.views.generic import RedirectView
from . import views
import re

def _url_prefix_path(url):
    """Return a URL path without leading/trailing slashes for regex routes."""
    return url.split('://', 1)[-1].split('/', 1)[-1].strip('/')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('site-logo/', views.site_logo, name='site_logo'),
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
    path("webhooks/", include("webhooks.urls")),
    path("activity-monitor/", include("activity_monitor.urls", namespace="activity_monitor")),
    path("ai-assistant/", include("ai_assistant.urls", namespace="ai_assistant")),
    path('gantt-test/', views.gantt_test, name='gantt_test'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
else:
    # Serve static files in production (logo, CSS, JS) when DEBUG is False
    static_path = _url_prefix_path(settings.STATIC_URL)
    media_path = _url_prefix_path(settings.MEDIA_URL)
    # Passenger may either preserve the mount prefix (/PMD) or strip it before
    # passing PATH_INFO to Django. Support both request forms.
    static_route = rf'^(?:{re.escape(static_path)}/|static/)' if static_path != 'static' else r'^static/'
    media_route = rf'^(?:{re.escape(media_path)}/|media/)' if media_path != 'media' else r'^media/'
    urlpatterns += [
        re_path(static_route + r'(?P<path>.*)$', static_serve, {'document_root': settings.STATIC_ROOT}),
    ]
    urlpatterns += [
        re_path(media_route + r'(?P<path>.*)$', static_serve, {'document_root': settings.MEDIA_ROOT}),
    ]
