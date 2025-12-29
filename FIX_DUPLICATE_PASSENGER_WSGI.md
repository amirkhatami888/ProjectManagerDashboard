# Fix: Duplicate passenger_wsgi.py Files

## Problem

You have TWO `passenger_wsgi.py` files:
1. ❌ `/home/ufvuikiv/public_html/PMD/passenger_wsgi.py` (WRONG location)
2. ✅ `/home/ufvuikiv/public_html/PMD/ProjectManagerDashboard/passenger_wsgi.py` (CORRECT location)

This is causing cPanel to get confused about which file to use.

## Solution

### Step 1: Remove the duplicate file

Delete the file in the PMD directory (not in ProjectManagerDashboard):

```bash
rm ~/public_html/PMD/passenger_wsgi.py
```

Or use the script:
```bash
bash fix_duplicate_passenger_wsgi.sh
```

### Step 2: Update cPanel Settings

In cPanel "Setup Python App", use these **exact** settings:

| Field | Value |
|-------|-------|
| **App Directory** | `public_html/PMD/ProjectManagerDashboard` |
| **Application startup file** | `passenger_wsgi.py` |
| **Application Entry point** | `application` |

### Step 3: Restart the App

1. Click "Save" in cPanel
2. Click "Restart" for your Python app

## Verify

After fixing, verify only one file exists:

```bash
find ~/public_html -name "passenger_wsgi.py"
```

Should only show:
```
/home/ufvuikiv/public_html/PMD/ProjectManagerDashboard/passenger_wsgi.py
```

## Why This Happened

The duplicate file in `/PMD/` directory is confusing cPanel. It might be trying to use that file instead of the one in `ProjectManagerDashboard/`.

## After Fix

Once you remove the duplicate and update cPanel settings, the error should be resolved!

