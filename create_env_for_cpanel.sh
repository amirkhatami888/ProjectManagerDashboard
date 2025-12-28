#!/bin/bash
# Script to create .env file for cPanel deployment

echo "Creating .env file for cPanel deployment..."

# Generate a secure SECRET_KEY
SECRET_KEY=$(python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")

cat > .env << EOF
# Production Environment Variables for cPanel
# Generated automatically - DO NOT commit this file to version control!

# Django Settings
SECRET_KEY=$SECRET_KEY
DEBUG=False
DJANGO_SETTINGS_MODULE=project_dashboard.production_settings

# Domain Configuration (Update with your actual domain)
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database Configuration - cPanel MySQL
DB_ENGINE=django.db.backends.mysql
DB_NAME=ufvuikiv_project_manager_db
DB_USER=ufvuikiv_amirkhatatmi888
DB_PASSWORD=Amir137667318@
DB_HOST=localhost
DB_PORT=3306

# Static and Media Files
STATIC_URL=/static/
MEDIA_URL=/media/

# Security Settings (Enable for HTTPS)
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SESSION_SECURE_COOKIES=True
SESSION_CSRF_COOKIE_SECURE=True

# Email Configuration (Optional)
EMAIL_HOST=localhost
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
EOF

echo "✅ .env file created successfully!"
echo "📝 Please update ALLOWED_HOSTS with your actual domain name"
echo "🔒 File permissions set to 600 (read/write for owner only)"
chmod 600 .env

