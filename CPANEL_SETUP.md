# cPanel Python App Setup Instructions

## Application Configuration in cPanel

When setting up your Python application in cPanel's "Setup Python App", use these settings:

### Required Fields:

1. **Python Version**: 
   - Select: `3.10` (or the version you're using)

2. **App Directory**: 
   - Path: `public_html/PMD/ProjectManagerDashboard`
   - Or: `public_html/ProjectManagerDashboard` (if directly in public_html)

3. **App URL**: 
   - `/` (for root domain)
   - Or: `/PMD` (if in subdirectory)

4. **Application startup file**: 
   - **File name**: `passenger_wsgi.py`
   - **Full path**: `public_html/PMD/ProjectManagerDashboard/passenger_wsgi.py`
   - **⚠️ IMPORTANT**: The file must be in the ROOT directory (same level as `manage.py`), NOT inside `project_dashboard/` folder!

5. **Application Entry point**: 
   - **Variable name**: `application`
   - This is the WSGI callable object that Passenger will use

### Summary:

```
Application startup file: passenger_wsgi.py
Application Entry point: application
```

---

## What's in passenger_wsgi.py?

The `passenger_wsgi.py` file contains:

```python
import sys
import os

# Add project directory to Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project_dashboard.production_settings')

# Import WSGI application
from project_dashboard.wsgi import application
```

This file:
1. Sets up the Python path so Django can find all modules
2. Configures Django to use production settings
3. Imports the `application` object from Django's WSGI module

---

## Step-by-Step cPanel Setup

### 1. Create Python App

1. Login to cPanel
2. Go to **"Setup Python App"** (under Software section)
3. Click **"Create Application"**

### 2. Fill in the Form

- **Python Version**: `3.10` (or your version)
- **App Directory**: `public_html/PMD/ProjectManagerDashboard`
- **App URL**: `/` or `/PMD` (depending on your setup)
- **Application startup file**: `passenger_wsgi.py`
- **Application Entry point**: `application`

### 3. Click "Create"

cPanel will:
- Create a virtual environment
- Set up Passenger to serve your app
- Generate a startup script

### 4. Install Dependencies

After creating the app, SSH into your server and run:

```bash
cd ~/public_html/PMD/ProjectManagerDashboard
source ~/virtualenv/public_html/PMD/3.10/bin/activate
pip install -r requirements.txt
```

### 5. Configure Environment

Create `.env` file (see `DEPLOY_CPANEL.md` for details)

### 6. Run Migrations

```bash
python manage.py migrate
python manage.py collectstatic --noinput
```

### 7. Restart Application

In cPanel "Setup Python App", click **"Restart"** for your application.

---

## Troubleshooting

### If you get "No module named 'project_dashboard'"

- Check that `passenger_wsgi.py` is in the correct directory
- Verify the App Directory path in cPanel matches your actual directory
- Make sure `sys.path.insert(0, project_dir)` is in `passenger_wsgi.py`

### If you get "application not found"

- Verify Application Entry point is exactly: `application` (lowercase)
- Check that `passenger_wsgi.py` imports: `from project_dashboard.wsgi import application`

### If you get "Settings module not found"

- Verify `.env` file exists with `DJANGO_SETTINGS_MODULE=project_dashboard.production_settings`
- Or ensure `passenger_wsgi.py` sets: `os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project_dashboard.production_settings')`

### Check Logs

```bash
# Check Passenger error logs
tail -f ~/logs/python_app.log

# Check Django logs
tail -f ~/public_html/PMD/ProjectManagerDashboard/logs/django.log
```

---

## Alternative: Direct WSGI Import

If `passenger_wsgi.py` doesn't work, you can also use:

**Application startup file**: `project_dashboard/wsgi.py`  
**Application Entry point**: `application`

But `passenger_wsgi.py` is recommended as it's in the root directory and easier to configure.

