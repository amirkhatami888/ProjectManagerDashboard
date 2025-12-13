from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .brute_force_views import BruteForceProtectedLoginView, refresh_captcha

app_name = 'accounts'

urlpatterns = [
    path('login/', BruteForceProtectedLoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('password_change/', auth_views.PasswordChangeView.as_view(template_name='accounts/password_change.html'), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='accounts/password_change_done.html'), name='password_change_done'),
    path('refresh-captcha/', refresh_captcha, name='refresh_captcha'),
] 