from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import User
from django.utils import timezone
from django.http import HttpRequest
from django.core.exceptions import ObjectDoesNotExist
import traceback
import json

from .utils import (
    log_activity, track_user_session, update_session_activity, 
    end_user_session, log_system_event
)


class ActivityTrackingMiddleware(MiddlewareMixin):
    """
    Middleware to automatically track user activities and sessions
    """
    
    def process_request(self, request: HttpRequest):
        """Process incoming request and track session activity"""
        # Skip tracking for static files and admin media
        if request.path.startswith(('/static/', '/media/', '/admin/jsi18n/')):
            return None
        
        # Track session activity if user is authenticated
        if request.user.is_authenticated and hasattr(request, 'session'):
            session_key = request.session.session_key
            if session_key:
                # Update session activity
                from .utils import update_session_activity, cleanup_expired_sessions
                update_session_activity(session_key)
                
                # Periodically clean up expired sessions (every 100 requests)
                if hasattr(request, '_request_count'):
                    request._request_count += 1
                else:
                    request._request_count = 1
                
                if request._request_count % 100 == 0:
                    cleanup_expired_sessions()
        
        # Store request start time for performance tracking
        request._activity_start_time = timezone.now()
        
        return None
    
    def process_response(self, request: HttpRequest, response):
        """Process response and log activities"""
        # Skip tracking for static files and admin media
        if request.path.startswith(('/static/', '/media/', '/admin/jsi18n/')):
            return response
        
        try:
            # Track page views for authenticated users
            if request.user.is_authenticated:
                self._track_page_view(request, response)
            
            # Track performance issues
            if hasattr(request, '_activity_start_time'):
                duration = (timezone.now() - request._activity_start_time).total_seconds()
                if duration > 5.0:  # Log slow requests
                    log_system_event(
                        event_type='PERFORMANCE',
                        title='Slow Request Detected',
                        description=f'Request to {request.path} took {duration:.2f} seconds',
                        severity='MEDIUM',
                        component='Middleware',
                        details={
                            'path': request.path,
                            'method': request.method,
                            'duration': duration,
                            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                        }
                    )
            
            # Track error responses
            if response.status_code >= 400:
                self._track_error_response(request, response)
                
        except Exception as e:
            # Log middleware errors without breaking the application
            print(f"Activity tracking middleware error: {e}")
        
        return response
    
    def process_exception(self, request: HttpRequest, exception):
        """Process exceptions and log them"""
        try:
            log_system_event(
                event_type='ERROR',
                title=f'Exception: {type(exception).__name__}',
                description=str(exception),
                severity='HIGH',
                component='Middleware',
                stack_trace=traceback.format_exc(),
                details={
                    'path': request.path,
                    'method': request.method,
                    'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                    'user': request.user.username if request.user.is_authenticated else 'Anonymous',
                }
            )
        except Exception as e:
            print(f"Error logging exception: {e}")
        
        return None
    
    def _track_page_view(self, request: HttpRequest, response):
        """Track page view activity"""
        if request.user.is_authenticated:
            # Skip tracking for AJAX requests and API calls
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return
            
            # Determine activity type based on request method
            if request.method == 'GET':
                activity_type = 'VIEW'
                description = f'Viewed {request.path}'
            elif request.method == 'POST':
                activity_type = 'UPDATE'
                description = f'Submitted form to {request.path}'
            else:
                activity_type = 'VIEW'
                description = f'Accessed {request.path}'
            
            # Log the activity
            log_activity(
                activity_type=activity_type,
                description=description,
                user=request.user,
                request=request,
                details={
                    'path': request.path,
                    'method': request.method,
                    'status_code': response.status_code,
                }
            )
    
    def _track_error_response(self, request: HttpRequest, response):
        """Track error responses"""
        if request.user.is_authenticated:
            severity = 'HIGH' if response.status_code >= 500 else 'MEDIUM'
            
            log_system_event(
                event_type='ERROR',
                title=f'HTTP {response.status_code} Error',
                description=f'Error response for {request.path}',
                severity=severity,
                component='HTTP',
                details={
                    'path': request.path,
                    'method': request.method,
                    'status_code': response.status_code,
                    'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                    'user': request.user.username,
                }
            )


class LoginLogoutMiddleware(MiddlewareMixin):
    """
    Middleware to track login and logout events
    """
    
    def process_request(self, request: HttpRequest):
        """Track login events"""
        # Track login
        if (request.path == '/accounts/login/' and 
            request.method == 'POST' and 
            request.user.is_authenticated):
            
            # Check if this is a successful login
            if hasattr(request, 'session') and request.session.session_key:
                # Track the new session
                track_user_session(request.user, request.session.session_key, request)
                
                # Log the login activity
                log_activity(
                    activity_type='LOGIN',
                    description=f'User {request.user.username} logged in successfully',
                    user=request.user,
                    request=request,
                    details={
                        'login_method': 'form',
                        'ip_address': self._get_client_ip(request),
                    }
                )
        
        return None
    
    def _get_client_ip(self, request: HttpRequest) -> str:
        """Extract client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class ProjectChangeMiddleware(MiddlewareMixin):
    """
    Middleware to track project-related changes
    """
    
    def process_request(self, request: HttpRequest):
        """Track project changes"""
        # Track project-related POST requests
        if (request.method == 'POST' and 
            request.user.is_authenticated and
            any(path in request.path for path in ['/projects/', '/subprojects/', '/programs/'])):
            
            # Store request data for processing in response
            request._is_project_change = True
            request._project_change_path = request.path
        
        return None
    
    def process_response(self, request: HttpRequest, response):
        """Process project change responses"""
        if (hasattr(request, '_is_project_change') and 
            request._is_project_change and 
            response.status_code in [200, 302]):
            
            try:
                # Determine change type based on path
                path = request._project_change_path
                if 'create' in path or 'add' in path:
                    change_type = 'CREATE'
                elif 'update' in path or 'edit' in path:
                    change_type = 'UPDATE'
                elif 'delete' in path:
                    change_type = 'DELETE'
                else:
                    change_type = 'UPDATE'
                
                # Log the project change
                log_activity(
                    activity_type=change_type,
                    description=f'Project change: {change_type.lower()} operation on {path}',
                    user=request.user,
                    request=request,
                    details={
                        'path': path,
                        'change_type': change_type,
                        'status_code': response.status_code,
                    }
                )
                
            except Exception as e:
                print(f"Error tracking project change: {e}")
        
        return response


class SecurityMiddleware(MiddlewareMixin):
    """
    Middleware to track security-related events
    """
    
    def process_request(self, request: HttpRequest):
        """Track security events"""
        # Track failed login attempts
        if (request.path == '/accounts/login/' and 
            request.method == 'POST' and 
            not request.user.is_authenticated):
            
            # This is a failed login attempt
            log_system_event(
                event_type='SECURITY',
                title='Failed Login Attempt',
                description=f'Failed login attempt from IP {self._get_client_ip(request)}',
                severity='MEDIUM',
                component='Authentication',
                details={
                    'ip_address': self._get_client_ip(request),
                    'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                    'path': request.path,
                }
            )
        
        # Track access to sensitive areas
        sensitive_paths = ['/admin/', '/activity-monitor/', '/api/']
        if any(path in request.path for path in sensitive_paths):
            if not request.user.is_authenticated:
                log_system_event(
                    event_type='SECURITY',
                    title='Unauthorized Access Attempt',
                    description=f'Unauthorized access attempt to {request.path}',
                    severity='HIGH',
                    component='Authorization',
                    details={
                        'ip_address': self._get_client_ip(request),
                        'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                        'path': request.path,
                    }
                )
        
        return None
    
    def _get_client_ip(self, request: HttpRequest) -> str:
        """Extract client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
