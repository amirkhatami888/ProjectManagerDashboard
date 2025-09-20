@echo off
echo Starting Django deployment to IIS...

REM Set environment variables for production
set DJANGO_SETTINGS_MODULE=project_dashboard.production_settings
set DEBUG=False
set SECRET_KEY=your-production-secret-key-here
set DB_ENGINE=django.db.backends.mysql
set DB_NAME=project_manager_db
set DB_USER=root
set DB_PASSWORD=your-db-password
set DB_HOST=localhost
set DB_PORT=3306
set ALLOWED_HOSTS=your-domain.com,www.your-domain.com,localhost,127.0.0.1
set SECURE_SSL_REDIRECT=True
set SESSION_COOKIE_SECURE=True
set SESSION_SECURE_COOKIES=True
set SESSION_CSRF_COOKIE_SECURE=True

echo Collecting static files...
python manage.py collectstatic --noinput --settings=project_dashboard.production_settings

echo Running database migrations...
python manage.py migrate --settings=project_dashboard.production_settings

echo Creating superuser if not exists...
python manage.py shell --settings=project_dashboard.production_settings -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superuser created')
else:
    print('Superuser already exists')
"

echo Deployment completed!
echo Make sure to:
echo 1. Update the web.config PYTHONPATH to match your deployment directory
echo 2. Configure your database connection
echo 3. Set up SSL certificate for HTTPS
echo 4. Configure IIS Application Pool for Python
echo 5. Install wfastcgi module
