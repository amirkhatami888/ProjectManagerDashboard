# Fix: BAD REQUEST 3 Error in cPanel

## Problem

You're getting "BAD REQUEST 3" error because the path to `passenger_wsgi.py` is incorrect.

## ❌ Wrong Path (What you're using):
```
public_html/PMD/ProjectManagerDashboard/project_dashboard/passenger_wsgi.py
```

## ✅ Correct Path (What you should use):
```
public_html/PMD/ProjectManagerDashboard/passenger_wsgi.py
```

---

## Solution

### Step 1: Verify File Location

SSH into your cPanel server and check:

```bash
cd ~/public_html/PMD/ProjectManagerDashboard
ls -la passenger_wsgi.py
```

The file should be in the **root directory** (same level as `manage.py`), NOT inside `project_dashboard/` folder.

### Step 2: Correct cPanel Settings

In cPanel "Setup Python App", use these **exact** settings:

| Field | Value |
|-------|-------|
| **App Directory** | `public_html/PMD/ProjectManagerDashboard` |
| **Application startup file** | `passenger_wsgi.py` |
| **Application Entry point** | `application` |

**⚠️ Important Notes:**
- Do NOT include `project_dashboard/` in the path
- The startup file should be just: `passenger_wsgi.py` (not a full path)
- cPanel will look for it in the App Directory you specified

### Step 3: File Structure Should Be:

```
public_html/PMD/ProjectManagerDashboard/
├── manage.py                    ← Root level
├── passenger_wsgi.py            ← Root level (THIS IS THE ONE!)
├── requirements.txt
├── .env
├── project_dashboard/
│   ├── wsgi.py                  ← This is different, don't use this
│   ├── settings.py
│   └── ...
├── accounts/
├── dashboard/
└── ...
```

### Step 4: If File is in Wrong Location

If `passenger_wsgi.py` is inside `project_dashboard/` folder, move it:

```bash
cd ~/public_html/PMD/ProjectManagerDashboard
mv project_dashboard/passenger_wsgi.py ./passenger_wsgi.py
```

Or if it doesn't exist, create it in the root:

```bash
cd ~/public_html/PMD/ProjectManagerDashboard
cat > passenger_wsgi.py << 'EOF'
import sys
import os

project_dir = os.path.dirname(os.path.abspath(__file__))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

os.chdir(project_dir)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project_dashboard.production_settings')

from project_dashboard.wsgi import application
EOF

chmod 644 passenger_wsgi.py
```

### Step 5: Restart Application

1. Go to cPanel → Setup Python App
2. Find your application
3. Click **"Restart"**

---

## Common "BAD REQUEST" Errors

### BAD REQUEST 3
- **Cause**: File path incorrect or file doesn't exist
- **Fix**: Use `passenger_wsgi.py` in root directory, not in subdirectory

### BAD REQUEST 4
- **Cause**: Application entry point (`application`) not found
- **Fix**: Make sure `from project_dashboard.wsgi import application` works

### BAD REQUEST 5
- **Cause**: Syntax error in startup file
- **Fix**: Check `passenger_wsgi.py` for syntax errors

---

## Verify Setup

Test if the file is correct:

```bash
cd ~/public_html/PMD/ProjectManagerDashboard
source ~/virtualenv/public_html/PMD/3.10/bin/activate
python -c "import sys; sys.path.insert(0, '.'); from project_dashboard.wsgi import application; print('✅ Import successful!')"
```

If this works, your `passenger_wsgi.py` should work too.

---

## Still Having Issues?

1. **Check file permissions:**
   ```bash
   chmod 644 passenger_wsgi.py
   ```

2. **Check error logs:**
   ```bash
   tail -f ~/logs/python_app.log
   tail -f ~/public_html/PMD/ProjectManagerDashboard/logs/django.log
   ```

3. **Verify Django is installed:**
   ```bash
   source ~/virtualenv/public_html/PMD/3.10/bin/activate
   python -c "import django; print(django.get_version())"
   ```

4. **Test WSGI import manually:**
   ```bash
   cd ~/public_html/PMD/ProjectManagerDashboard
   python passenger_wsgi.py
   ```

