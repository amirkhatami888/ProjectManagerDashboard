from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone
from django.conf import settings
from .models import SessionSecurity
import logging

logger = logging.getLogger(__name__)


class SessionSecurityMiddleware(MiddlewareMixin):
    """Enhanced session security middleware"""
    
    def process_request(self, request):
        if hasattr(request, 'user') and request.user.is_authenticated:
            # Get or create session security record
            security, created = SessionSecurity.objects.get_or_create(
                user=request.user,
                defaults={'failed_attempts': 0, 'is_locked': False}
            )
            
            # Check if user is locked out
            if security.is_locked and security.lockout_until:
                if timezone.now() < security.lockout_until:
                    # Still locked out
                    logger.warning(f"User {request.user.username} is locked out until {security.lockout_until}")
                    return None
                else:
                    # Lockout period expired, reset
                    security.is_locked = False
                    security.lockout_until = None
                    security.failed_attempts = 0
                    security.save()
        
        return None
    
    def process_response(self, request, response):
        # Handle failed login attempts
        if hasattr(request, 'user') and request.user.is_authenticated:
            if hasattr(request, 'login_failed') and request.login_failed:
                self.handle_failed_login(request.user)
        
        return response
    
    def handle_failed_login(self, user):
        """Handle failed login attempt"""
        security, created = SessionSecurity.objects.get_or_create(
            user=user,
            defaults={'failed_attempts': 0, 'is_locked': False}
        )
        
        security.failed_attempts += 1
        security.last_failed_attempt = timezone.now()
        
        # Check if user should be locked out
        max_attempts = getattr(settings, 'SESSION_MAX_FAILED_ATTEMPTS', 5)
        if security.failed_attempts >= max_attempts:
            security.is_locked = True
            lockout_duration = getattr(settings, 'SESSION_LOCKOUT_DURATION', 300)
            security.lockout_until = timezone.now() + timezone.timedelta(seconds=lockout_duration)
            logger.warning(f"User {user.username} locked out for {lockout_duration} seconds")
        
        security.save()
