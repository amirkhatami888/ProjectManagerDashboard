from django.utils.deprecation import MiddlewareMixin
from django.contrib.sessions.models import Session
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings
from .models import SessionLog, SessionSecurity
import logging

logger = logging.getLogger(__name__)


class SessionExpiryMiddleware(MiddlewareMixin):
    """Middleware to handle session expiry and cleanup"""
    
    def process_request(self, request):
        if hasattr(request, 'user') and request.user.is_authenticated:
            # Check if session is expired
            if request.session.get_expiry_age() <= 0:
                request.session.flush()
                logger.info(f"Session expired for user: {request.user.username}")
        
        return None


class SessionLoggingMiddleware(MiddlewareMixin):
    """Middleware to log session activity"""
    
    def process_request(self, request):
        if hasattr(request, 'user') and request.user.is_authenticated:
            session_key = request.session.session_key
            if session_key:
                # Get or create session log
                session_log, created = SessionLog.objects.get_or_create(
                    session_key=session_key,
                    defaults={
                        'user': request.user,
                        'ip_address': self.get_client_ip(request),
                        'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                        'is_active': True
                    }
                )
                
                if not created:
                    # Update last activity
                    session_log.last_activity = timezone.now()
                    session_log.save()
        
        return None
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SessionSecurityMiddleware(MiddlewareMixin):
    """Middleware to handle session security and lockout"""
    
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
