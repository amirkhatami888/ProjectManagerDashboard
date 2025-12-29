# Fix: "No such WSGI script" Error with Duplicate Path

## Problem

The error shows a duplicate path:
```
/home/ufvuikiv/public_html/PMD/public_html/PMD/Project...
```

This means cPanel is adding `public_html/PMD/` twice.

## Solution

The **App Directory** in cPanel should be relative to your home directory, NOT include `public_html/`.

### Correct Settings:

| Field | Correct Value |
|-------|---------------|
| **App Directory** | `PMD/ProjectManagerDashboard` |
| **Application startup file** | `passenger_wsgi.py` |
| **Application Entry point** | `application` |

### ❌ Wrong (causes duplicate path):
- App Directory: `public_html/PMD/ProjectManagerDashboard`

### ✅ Correct:
- App Directory: `PMD/ProjectManagerDashboard`

## Step-by-Step Fix

1. **Go to cPanel → Setup Python App**
2. **Edit your existing application** (or create new)
3. **Set App Directory to**: `PMD/ProjectManagerDashboard`
   - Do NOT include `public_html/` in the path
   - cPanel automatically knows your home directory
4. **Set Application startup file to**: `passenger_wsgi.py`
5. **Set Application Entry point to**: `application`
6. **Click "Save"**
7. **Click "Restart"**

## Verify File Location

Make sure `passenger_wsgi.py` exists in the correct location:

```bash
ls -la ~/public_html/PMD/ProjectManagerDashboard/passenger_wsgi.py
```

The file should exist at:
```
/home/ufvuikiv/public_html/PMD/ProjectManagerDashboard/passenger_wsgi.py
```

## Alternative: Use Full Path (if relative doesn't work)

If using relative path doesn't work, some cPanel versions require:

**App Directory**: `public_html/PMD/ProjectManagerDashboard`

But then make sure the **Application startup file** is just:
`passenger_wsgi.py`

(Not a full path, just the filename)

## Quick Test

After fixing, check the error logs:
```bash
tail -f ~/logs/python_app.log
```

The path should now be:
```
/home/ufvuikiv/public_html/PMD/ProjectManagerDashboard/passenger_wsgi.py
```

NOT:
```
/home/ufvuikiv/public_html/PMD/public_html/PMD/ProjectManagerDashboard/passenger_wsgi.py
```

