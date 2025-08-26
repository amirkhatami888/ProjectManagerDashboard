from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponseRedirect
from django.urls import reverse
from .forms import UserProfileForm

# Create your views here.

def custom_logout(request):
    """Custom logout view that handles both GET and POST requests"""
    if request.user.is_authenticated:
        # Log the logout action if you have activity monitoring
        try:
            from activity_monitor.utils import log_activity
            log_activity(
                activity_type='LOGOUT',
                description=f'User {request.user.username} logged out successfully',
                user=request.user,
                request=request,
                details={
                    'logout_method': 'manual',
                    'session_key': request.session.session_key if request.session else None,
                }
            )
        except ImportError:
            pass  # Activity monitoring not available
        
        # Clear the session
        request.session.flush()
        
        # Logout the user
        logout(request)
        
        messages.success(request, 'شما با موفقیت از سیستم خارج شدید.')
    
    # Redirect to login page
    return HttpResponseRedirect(reverse('login'))

@login_required
def profile(request):
    """View for users to see and edit their profile"""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'پروفایل شما با موفقیت به‌روزرسانی شد.')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=request.user)
    
    context = {
        'form': form
    }
    return render(request, 'accounts/profile.html', context)
