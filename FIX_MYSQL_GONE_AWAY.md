# Fix: MySQL server has gone away

## Problem

The error "MySQL server has gone away" occurs when:
- Connection times out
- Connection is closed by server
- Connection pool issues

## Solution Applied

I've updated `production_settings.py` with:
- Increased connection timeouts (60 seconds)
- Disabled persistent connections (`CONN_MAX_AGE: 0`)
- Added autocommit option

## Quick Fix: Create Superuser Directly

Instead of using `createsuperuser`, use the direct script:

```bash
python create_superuser_direct.py
```

This avoids connection timeout issues.

## Alternative: Increase MySQL Timeout

You can also increase MySQL's wait_timeout:

```bash
mysql -u ufvuikiv_amirkhatatmi888 -p'Amir137667318@' ufvuikiv_project_manager_db << 'EOF'
SET GLOBAL wait_timeout = 28800;
SET GLOBAL interactive_timeout = 28800;
EOF
```

## Or: Create Superuser via MySQL Directly

If Django keeps timing out, create the user directly in MySQL:

```bash
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project_dashboard.production_settings')
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
user = User.objects.create_user('amirkhatami888', 'email@example.com', 'your_password')
user.is_staff = True
user.is_superuser = True
user.save()
print('Superuser created!')
"
```

## Test Connection

Test if the connection works:

```bash
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project_dashboard.production_settings')
django.setup()
from django.db import connection
connection.ensure_connection()
print('Connection OK!')
"
```

