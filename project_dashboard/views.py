from html import escape
from pathlib import Path

from django.shortcuts import render
from django.conf import settings
from django.http import FileResponse, HttpResponse, Http404

def home(request):
    """
    Render the login page directly.
    """
    return render(request, 'accounts/login.html')


def site_logo(request):
    """Serve the login logo through Django when web-server static mapping fails."""
    logo_path = Path(settings.BASE_DIR) / 'static' / 'image' / 'logo.png'
    if not logo_path.is_file():
        raise Http404("Logo file not found")
    return FileResponse(logo_path.open('rb'), content_type='image/png')


def debug_info(request):
    """
    Display debug information about the current URL and redirect settings.
    """
    html = """
    <html>
    <head><title>Debug Info</title></head>
    <body>
        <h1>Debug Information</h1>
        <p>Current URL path: {}</p>
        <p>Should redirect to: /accounts/login/</p>
        <p>Try these links:</p>
        <ul>
            <li><a href="/">Home (root URL)</a></li>
            <li><a href="/accounts/login/">Correct login URL</a></li>
            <li><a href="/user/login/">User login URL (should redirect)</a></li>
        </ul>
    </body>
    </html>
    """.format(escape(request.path))
    return HttpResponse(html)

def gantt_test(request):
    """Simple test view for Gantt chart debugging"""
    return render(request, 'gantt_test.html')

def index(request):
    return HttpResponse("Project Dashboard - Index")
