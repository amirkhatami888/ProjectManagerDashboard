import os
from waitress import serve
from project_dashboard.wsgi import application

if __name__ == "__main__":
    # Set environment to use production settings
    os.environ.setdefault('DJANGO_ENV', 'production')
    
    # Get host and port from environment variables or use defaults
    host = os.environ.get('HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', 8000))
    
    print(f"Starting server on {host}:{port}")
    print(f"Using settings: {os.environ.get('DJANGO_SETTINGS_MODULE', 'project_dashboard.settings')}")
    
    serve(application, host=host, port=port)
