# Fix: cPanel App Directory Path Duplication

## Problem

Even with correct settings, cPanel is duplicating the path:
```
/home/ufvuikiv/public_html/PMD/public_html/PMD/Project...
```

This means cPanel is adding `public_html/PMD/` to your App Directory setting.

## Solutions to Try

### Solution 1: Use Only Subdirectory Name

If your Python app base is set to `public_html/PMD/`, then App Directory should be just:

| Field | Value |
|-------|-------|
| **App Directory** | `ProjectManagerDashboard` |
| **Application startup file** | `passenger_wsgi.py` |
| **Application Entry point** | `application` |

### Solution 2: Check Python App Base Directory

In cPanel, check what the **base directory** or **root directory** is set to for your Python app. It might be:
- `public_html/PMD/` (which would explain the duplication)

If so, set App Directory to: `ProjectManagerDashboard`

### Solution 3: Use Absolute Path

Try using the full absolute path:

| Field | Value |
|-------|-------|
| **App Directory** | `/home/ufvuikiv/public_html/PMD/ProjectManagerDashboard` |
| **Application startup file** | `passenger_wsgi.py` |
| **Application Entry point** | `application` |

### Solution 4: Check App URL Setting

The **App URL** might affect the path. Try:
- App URL: `/` or `/PMD`
- App Directory: `ProjectManagerDashboard` (relative to where App URL points)

## Most Likely Fix

**Try Solution 1 first**: Set App Directory to just `ProjectManagerDashboard` (without `public_html/PMD/`).

cPanel might already have `public_html/PMD/` as the base, so adding it again causes duplication.

## How to Check

Look at your Python app settings in cPanel. There should be a field showing the "base directory" or "root". That's what gets prepended to your App Directory.

