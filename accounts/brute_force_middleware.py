"""
Brute Force Protection Middleware for Django
Implements multiple layers of protection against brute-force attacks
"""
import time
import json
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
from django.contrib import messages
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

class BruteForceProtectionMiddleware(MiddlewareMixin):
    """
    Comprehensive brute-force protection middleware
    Implements IP-based blocking, progressive delays, and account lockout
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.async_mode = False
        # Configuration from settings
        self.max_attempts_per_ip = getattr(settings, 'BRUTE_FORCE_MAX_ATTEMPTS_PER_IP', 10)
        self.max_attempts_per_user = getattr(settings, 'BRUTE_FORCE_MAX_ATTEMPTS_PER_USER', 5)
        self.lockout_duration = getattr(settings, 'BRUTE_FORCE_LOCKOUT_DURATION', 900)  # 15 minutes
        self.progressive_delay_base = getattr(settings, 'BRUTE_FORCE_PROGRESSIVE_DELAY_BASE', 2)  # seconds
        self.captcha_threshold = getattr(settings, 'BRUTE_FORCE_CAPTCHA_THRESHOLD', 3)
        
    def process_request(self, request):
        """Process incoming request for brute-force protection"""
        # Only apply to login attempts
        if not (request.path == '/accounts/login/' and request.method == 'POST'):
            return None
            
        # Get client IP
        client_ip = self._get_client_ip(request)
        username = request.POST.get('username', '').strip()
        
        # Check if IP is blocked
        if self._is_ip_blocked(client_ip):
            logger.warning(f"Blocked login attempt from blocked IP: {client_ip}")
            return self._create_blocked_response(request, "IP address is temporarily blocked due to too many failed attempts.")
        
        # Check if user account is locked
        if username and self._is_user_locked(username):
            logger.warning(f"Blocked login attempt for locked user: {username}")
            return self._create_blocked_response(request, "Account is temporarily locked due to too many failed attempts.")
        
        # Check progressive delay
        delay = self._get_progressive_delay(client_ip, username)
        if delay > 0:
            logger.info(f"Applying progressive delay of {delay} seconds for {client_ip}")
            time.sleep(delay)
        
        return None
    
    def process_response(self, request, response):
        """Process response to track failed login attempts"""
        # Only process login responses
        if not (request.path == '/accounts/login/' and request.method == 'POST'):
            return response
            
        client_ip = self._get_client_ip(request)
        username = request.POST.get('username', '').strip()
        
        # Check if login was successful
        if hasattr(request, 'user') and request.user.is_authenticated:
            # Login successful - clear any existing failures
            self._clear_failed_attempts(client_ip, username)
            logger.info(f"Successful login for user {username} from IP {client_ip}")
        else:
            # Login failed - record the attempt
            self._record_failed_attempt(client_ip, username)
            
            # Check if we should show CAPTCHA
            if self._should_show_captcha(client_ip, username):
                # Add CAPTCHA flag to session
                request.session['show_captcha'] = True
                request.session['captcha_required'] = True
                
        return response
    
    def _get_client_ip(self, request):
        """Extract client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def _is_ip_blocked(self, ip):
        """Check if IP is blocked"""
        cache_key = f"brute_force_ip_blocked:{ip}"
        return cache.get(cache_key, False)
    
    def _is_user_locked(self, username):
        """Check if user account is locked"""
        cache_key = f"brute_force_user_locked:{username}"
        return cache.get(cache_key, False)
    
    def _get_progressive_delay(self, ip, username):
        """Calculate progressive delay based on failed attempts"""
        ip_attempts = self._get_failed_attempts_count(f"brute_force_ip_attempts:{ip}")
        user_attempts = self._get_failed_attempts_count(f"brute_force_user_attempts:{username}") if username else 0
        
        max_attempts = max(ip_attempts, user_attempts)
        
        if max_attempts <= 2:
            return 0
        elif max_attempts <= 5:
            return self.progressive_delay_base
        elif max_attempts <= 8:
            return self.progressive_delay_base * 2
        else:
            return self.progressive_delay_base * 4
    
    def _should_show_captcha(self, ip, username):
        """Determine if CAPTCHA should be shown"""
        ip_attempts = self._get_failed_attempts_count(f"brute_force_ip_attempts:{ip}")
        user_attempts = self._get_failed_attempts_count(f"brute_force_user_attempts:{username}") if username else 0
        
        return max(ip_attempts, user_attempts) >= self.captcha_threshold
    
    def _get_failed_attempts_count(self, cache_key):
        """Get count of failed attempts"""
        attempts_data = cache.get(cache_key, [])
        # Clean old attempts (older than lockout duration)
        current_time = time.time()
        recent_attempts = [attempt for attempt in attempts_data if current_time - attempt < self.lockout_duration]
        return len(recent_attempts)
    
    def _record_failed_attempt(self, ip, username):
        """Record a failed login attempt"""
        current_time = time.time()
        
        # Record IP attempt
        ip_cache_key = f"brute_force_ip_attempts:{ip}"
        ip_attempts = cache.get(ip_cache_key, [])
        ip_attempts.append(current_time)
        cache.set(ip_cache_key, ip_attempts, self.lockout_duration)
        
        # Record user attempt if username provided
        if username:
            user_cache_key = f"brute_force_user_attempts:{username}"
            user_attempts = cache.get(user_cache_key, [])
            user_attempts.append(current_time)
            cache.set(user_cache_key, user_attempts, self.lockout_duration)
        
        # Check if IP should be blocked
        if len(ip_attempts) >= self.max_attempts_per_ip:
            self._block_ip(ip)
            logger.warning(f"IP {ip} blocked due to {len(ip_attempts)} failed attempts")
        
        # Check if user should be locked
        if username and len(user_attempts) >= self.max_attempts_per_user:
            self._lock_user(username)
            logger.warning(f"User {username} locked due to {len(user_attempts)} failed attempts")
    
    def _block_ip(self, ip):
        """Block an IP address"""
        cache_key = f"brute_force_ip_blocked:{ip}"
        cache.set(cache_key, True, self.lockout_duration)
    
    def _lock_user(self, username):
        """Lock a user account"""
        cache_key = f"brute_force_user_locked:{username}"
        cache.set(cache_key, True, self.lockout_duration)
    
    def _clear_failed_attempts(self, ip, username):
        """Clear failed attempts after successful login"""
        cache.delete(f"brute_force_ip_attempts:{ip}")
        if username:
            cache.delete(f"brute_force_user_attempts:{username}")
    
    def _create_blocked_response(self, request, message):
        """Create response for blocked requests"""
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'error': message,
                'blocked': True,
                'retry_after': self.lockout_duration
            }, status=429)
        else:
            # Add message to session for display on login page
            request.session['brute_force_message'] = message
            request.session['brute_force_blocked'] = True
            return None  # Let the request continue to show the message
