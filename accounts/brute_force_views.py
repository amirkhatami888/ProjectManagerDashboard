"""
Enhanced Login View with Brute Force Protection
Custom login view that integrates with brute-force protection middleware
"""
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.conf import settings
import json
import logging

from .captcha import SimpleCaptcha

logger = logging.getLogger(__name__)

class BruteForceProtectedLoginView(LoginView):
    """Enhanced login view with brute-force protection"""
    
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True
    
    def get_context_data(self, **kwargs):
        """Add brute-force protection context to template"""
        context = super().get_context_data(**kwargs)
        
        # Check if CAPTCHA is required
        if self.request.session.get('show_captcha', False):
            captcha = SimpleCaptcha()
            captcha_data = captcha.generate_captcha(self.request.session.session_key)
            context['captcha'] = captcha_data
            context['show_captcha'] = True
        
        # Check for brute-force messages
        if self.request.session.get('brute_force_message'):
            context['brute_force_message'] = self.request.session.pop('brute_force_message')
            context['brute_force_blocked'] = self.request.session.pop('brute_force_blocked', False)
        
        # Add security information
        context['max_attempts'] = getattr(settings, 'BRUTE_FORCE_MAX_ATTEMPTS_PER_IP', 10)
        context['lockout_duration'] = getattr(settings, 'BRUTE_FORCE_LOCKOUT_DURATION', 900)
        
        return context
    
    def form_valid(self, form):
        """Handle valid form submission with additional security checks"""
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        captcha_id = self.request.POST.get('captcha_id')
        captcha_answer = self.request.POST.get('captcha_answer')
        
        # Verify CAPTCHA if required
        if self.request.session.get('captcha_required', False):
            if not captcha_id or not captcha_answer:
                messages.error(self.request, 'لطفاً مسئله امنیتی را حل کنید.')
                return self.form_invalid(form)
            
            captcha = SimpleCaptcha()
            if not captcha.verify_captcha(captcha_id, captcha_answer):
                messages.error(self.request, 'پاسخ مسئله امنیتی اشتباه است.')
                return self.form_invalid(form)
            
            # Clear CAPTCHA requirement after successful verification
            self.request.session.pop('captcha_required', None)
            self.request.session.pop('show_captcha', None)
        
        # Authenticate user
        user = authenticate(self.request, username=username, password=password)
        
        if user is not None:
            if user.is_active:
                login(self.request, user)
                
                # Log successful login
                logger.info(f"Successful login for user {username} from IP {self.get_client_ip()}")
                
                # Clear any brute-force flags
                self.clear_brute_force_flags()
                
                # Redirect to next page or dashboard
                next_url = self.get_success_url()
                if self.request.POST.get('next'):
                    next_url = self.request.POST.get('next')
                
                if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'redirect_url': next_url,
                        'message': 'ورود موفقیت‌آمیز'
                    })
                
                return redirect(next_url)
            else:
                messages.error(self.request, 'حساب کاربری شما غیرفعال است.')
        else:
            messages.error(self.request, 'نام کاربری یا رمز عبور اشتباه است.')
        
        return self.form_invalid(form)
    
    def form_invalid(self, form):
        """Handle invalid form submission"""
        # The brute-force middleware will handle failed attempt tracking
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'errors': form.errors,
                'message': 'اطلاعات وارد شده صحیح نیست.'
            })
        
        return super().form_invalid(form)
    
    def get_client_ip(self):
        """Get client IP address"""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip
    
    def clear_brute_force_flags(self):
        """Clear brute-force protection flags after successful login"""
        session_keys_to_remove = [
            'show_captcha',
            'captcha_required',
            'brute_force_message',
            'brute_force_blocked'
        ]
        
        for key in session_keys_to_remove:
            self.request.session.pop(key, None)

@csrf_exempt
@require_http_methods(["POST"])
def refresh_captcha(request):
    """AJAX endpoint to refresh CAPTCHA"""
    if not request.session.get('show_captcha', False):
        return JsonResponse({'error': 'CAPTCHA not required'}, status=400)
    
    captcha = SimpleCaptcha()
    captcha_data = captcha.generate_captcha(request.session.session_key)
    
    return JsonResponse({
        'captcha_id': captcha_data['id'],
        'question': captcha_data['question']
    })




