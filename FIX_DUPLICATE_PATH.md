# Fix: Duplicate Path in cPanel Python App

## Problem

Even with correct settings, you're getting:
```
No such WSGI script "/home/ufvuikiv/public_html/PMD/public_html/PMD/Project...
```

This means cPanel is adding the path twice.

## Solutions to Try

### Solution 1: Use Absolute Path in App Directory

In cPanel "Setup Python App":

| Field | Value |
|-------|-------|
| **App Directory** | `/home/ufvuikiv/public_html/PMD/ProjectManagerDashboard` |
| **Application startup file** | `passenger_wsgi.py` |
| **Application Entry point** | `application` |

### Solution 2: Use Relative Path from Home

| Field | Value |
|-------|-------|
| **App Directory** | `public_html/PMD/ProjectManagerDashboard` |
| **Application startup file** | `passenger_wsgi.py` |
| **Application Entry point** | `application` |

### Solution 3: Check App URL Setting

Sometimes the **App URL** setting affects the path resolution:

- If App URL is `/PMD`, try setting App Directory to just: `ProjectManagerDashboard`
- Or try App Directory: `PMD/ProjectManagerDashboard` with App URL: `/`

### Solution 4: Delete and Recreate the App

1. Delete the existing Python app in cPanel
2. Create a new one with these exact settings:
   - **App Directory**: `public_html/PMD/ProjectManagerDashboard`
   - **App URL**: `/` or `/PMD`
   - **Application startup file**: `passenger_wsgi.py`
   - **Application Entry point**: `application`

## Verify Current Settings

Check what cPanel thinks the path is by looking at the app's configuration file:

```bash
cat ~/passenger_wsgi.py 2>/dev/null || echo "Not in home"
ls -la ~/public_html/PMD/ProjectManagerDashboard/passenger_wsgi.py
```

## Alternative: Create Symbolic Link

If nothing works, create a symlink in the expected location:

```bash
# Check where cPanel expects the file
# Then create symlink if needed
ln -s ~/public_html/PMD/ProjectManagerDashboard/passenger_wsgi.py ~/passenger_wsgi.py
```

## Most Common Fix

Try **Solution 2** first - use `public_html/PMD/ProjectManagerDashboard` as App Directory (with `public_html/` included).

Some cPanel versions require the full path from home directory.

