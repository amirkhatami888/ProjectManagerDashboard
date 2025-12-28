# Troubleshooting BAD REQUEST 3 Error

## What is BAD REQUEST 3?

This error means Passenger cannot find or load your startup file. Common causes:

1. **File path is incorrect** - File not in the right location
2. **File doesn't exist** - File not uploaded to server
3. **Syntax error** - Python syntax error in the file
4. **Import error** - Cannot import Django or modules
5. **File permissions** - File not readable

---

## Step-by-Step Fix

### Step 1: Verify File Exists on Server

SSH into your server and check:

```bash
cd ~/public_html/PMD/ProjectManagerDashboard
ls -la passenger_wsgi.py
```

**Expected output:**
```
-rw-r--r-- 1 username username 1234 date passenger_wsgi.py
```

If file doesn't exist, you need to upload it!

### Step 2: Check File Location

The file MUST be in the root directory:

```bash
cd ~/public_html/PMD/ProjectManagerDashboard
pwd
# Should show: /home/username/public_html/PMD/ProjectManagerDashboard

ls -la | grep passenger
# Should show: passenger_wsgi.py
```

**File structure should be:**
```
~/public_html/PMD/ProjectManagerDashboard/
├── passenger_wsgi.py    ← Must be here
├── manage.py
├── project_dashboard/
│   └── wsgi.py         ← Different file, don't use this
```

### Step 3: Test File Manually

Test if the file works:

```bash
cd ~/public_html/PMD/ProjectManagerDashboard
source ~/virtualenv/public_html/PMD/3.10/bin/activate
python passenger_wsgi.py
```

**If you get errors**, fix them first before using in cPanel.

### Step 4: Check cPanel Settings

In cPanel "Setup Python App":

1. **App Directory**: `public_html/PMD/ProjectManagerDashboard`
2. **Application startup file**: `passenger_wsgi.py` (just the filename, no path!)
3. **Application Entry point**: `application`

**⚠️ Common Mistakes:**
- ❌ `project_dashboard/passenger_wsgi.py` (WRONG - don't include subdirectory)
- ❌ `/home/username/public_html/PMD/ProjectManagerDashboard/passenger_wsgi.py` (WRONG - don't use full path)
- ✅ `passenger_wsgi.py` (CORRECT - just the filename)

### Step 5: Try Simpler Version

If still not working, try the simpler version:

1. Upload `passenger_wsgi_simple.py` to your server
2. Rename it to `passenger_wsgi.py`:
   ```bash
   cd ~/public_html/PMD/ProjectManagerDashboard
   mv passenger_wsgi_simple.py passenger_wsgi.py
   ```
3. Update cPanel to use `passenger_wsgi.py`

### Step 6: Check File Permissions

```bash
chmod 644 passenger_wsgi.py
chown username:username passenger_wsgi.py
```

### Step 7: Check Error Logs

```bash
# Passenger error log
tail -f ~/logs/python_app.log

# Or check cPanel error logs
# cPanel → Metrics → Errors
```

---

## Alternative: Use project_dashboard/wsgi.py Directly

If `passenger_wsgi.py` still doesn't work, try using Django's WSGI file directly:

**In cPanel:**
- **Application startup file**: `project_dashboard/wsgi.py`
- **Application Entry point**: `application`

But first, update `project_dashboard/wsgi.py` to use production settings:

```python
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project_dashboard.production_settings')
application = get_wsgi_application()
```

---

## Quick Diagnostic Script

Run this to check everything:

```bash
cd ~/public_html/PMD/ProjectManagerDashboard

echo "=== Checking passenger_wsgi.py ==="
ls -la passenger_wsgi.py

echo -e "\n=== Testing Python import ==="
source ~/virtualenv/public_html/PMD/3.10/bin/activate
python -c "import sys; sys.path.insert(0, '.'); exec(open('passenger_wsgi.py').read()); print('✅ File loads successfully!')"

echo -e "\n=== Checking Django ==="
python -c "import django; print(f'Django version: {django.get_version()}')"

echo -e "\n=== Checking WSGI import ==="
python -c "from project_dashboard.wsgi import application; print('✅ WSGI application imported!')"
```

---

## Most Common Solution

**90% of the time, the issue is:**

1. File not uploaded to server → **Upload it!**
2. Wrong path in cPanel → Use just `passenger_wsgi.py` (no subdirectory)
3. File in wrong location → Must be in root, not in `project_dashboard/`

**Quick fix:**
```bash
# On server
cd ~/public_html/PMD/ProjectManagerDashboard
cat > passenger_wsgi.py << 'EOF'
import sys
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.chdir(BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project_dashboard.production_settings')
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
EOF
chmod 644 passenger_wsgi.py
```

Then in cPanel, set:
- Application startup file: `passenger_wsgi.py`
- Application Entry point: `application`

