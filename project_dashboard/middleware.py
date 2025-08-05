import re
from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse

class LoginRequiredMiddleware:
    """
    Middleware that requires a user to be authenticated to view any page,
    except those defined in settings.EXEMPT_URLS.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.exempt_urls = [
            re.compile(r'^/accounts/login/.*$'),
            re.compile(r'^/accounts/logout/.*$'),
            re.compile(r'^/admin/.*$'),
            re.compile(r'^/static/.*$'),
            re.compile(r'^/media/.*$'),
            # Add other URLs that should be accessible without login
        ]
    
    def __call__(self, request):
        # Check if the path matches any exempt URLs
        path = request.path_info
        
        # Allow access to exempt URLs
        if any(pattern.match(path) for pattern in self.exempt_urls):
            return self.get_response(request)
        
        # Require login for all other URLs
        if not request.user.is_authenticated:
            # Use absolute URL for login
            login_url = '/accounts/login/'
            if '?' not in login_url:
                login_url += f'?next={path}'
            return redirect(login_url)
        
        return self.get_response(request) 