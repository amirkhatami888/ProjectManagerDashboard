cat > .env << 'EOF'
# Production Environment Variables for cPanel
# DO NOT commit this file to version control!

# Django Settings
SECRET_KEY=#+x1$zg#=h*^ky!_lzq(=bfg4t7=-$@cm7ln@b(!t#nmb)ue^h
DEBUG=False
DJANGO_SETTINGS_MODULE=project_dashboard.production_settings

# Domain Configuration
ALLOWED_HOSTS=projecthelal.rcs.ir,www.projecthelal.rcs.ir,localhost,127.0.0.1

# Database Configuration - cPanel MySQL
DB_ENGINE=django.db.backends.mysql
DB_NAME=ufvuikiv_project_manager_db
DB_USER=ufvuikiv_amirkhatatmi888
DB_PASSWORD=Amir137667318@
DB_HOST=localhost
DB_PORT=3306

# Security Settings
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
SESSION_SECURE_COOKIES=False
SESSION_CSRF_COOKIE_SECURE=False
EOF