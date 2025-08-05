from django.shortcuts import render
from django.http import HttpResponse

def home(request):
    """
    Render the login page directly.
    """
    return render(request, 'accounts/login.html')

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
    """.format(request.path)
    return HttpResponse(html) 