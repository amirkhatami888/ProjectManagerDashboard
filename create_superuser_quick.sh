#!/bin/bash
# Quick superuser creation using Django shell

cd ~/public_html/PMD/ProjectManagerDashboard

python << 'PYTHON_EOF'
# Use PyMySQL
import pymysql
pymysql.install_as_MySQLdb()

import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project_dashboard.production_settings')

# Remove django_extensions if not installed
import django
from django.conf import settings
if 'django_extensions' in settings.INSTALLED_APPS:
    try:
        import django_extensions
    except ImportError:
        settings.INSTALLED_APPS.remove('django_extensions')

django.setup()

from accounts.models import User

username = 'amirkhatami888'
email = input('Email: ').strip() or 'amirkhatami888@example.com'
password = input('Password: ').strip()

if not password:
    print('❌ Password required!')
    exit(1)

if User.objects.filter(username=username).exists():
    print(f'❌ User {username} already exists!')
    exit(1)

user = User.objects.create_user(username, email, password)
user.is_staff = True
user.is_superuser = True
user.save()
print(f'✅ Superuser {username} created!')
PYTHON_EOF

