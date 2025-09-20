# Django IIS Deployment Guide

## Prerequisites

1. **Windows Server with IIS installed**
2. **Python 3.9+ installed**
3. **MySQL Server installed**
4. **wfastcgi module installed**

## Step 1: Install Required Components

### Install Python
```bash
# Download and install Python 3.9+ from python.org
# Make sure to check "Add Python to PATH" during installation
```

### Install wfastcgi
```bash
pip install wfastcgi
```

### Install Project Dependencies
```bash
pip install -r requirements.txt
```

## Step 2: Configure IIS

### Enable Required IIS Features
1. Open **Server Manager**
2. Go to **Add Roles and Features**
3. Enable:
   - **Web Server (IIS)**
   - **CGI**
   - **FastCGI**
   - **URL Rewrite Module**

### Install URL Rewrite Module
Download and install from: https://www.iis.net/downloads/microsoft/url-rewrite

## Step 3: Database Setup

### Create MySQL Database
```sql
CREATE DATABASE project_manager_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'django_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON project_manager_db.* TO 'django_user'@'localhost';
FLUSH PRIVILEGES;
```

## Step 4: Deploy Application

### 1. Copy Project Files
Copy your Django project to: `C:\inetpub\wwwroot\ProjectManagerDashboard`

### 2. Update web.config
Update the `PYTHONPATH` in web.config to match your deployment directory:
```xml
<add key="PYTHONPATH" value="C:\inetpub\wwwroot\ProjectManagerDashboard" />
```

### 3. Configure Environment Variables
Copy `env.production` to `.env` and update the values:
```bash
copy env.production .env
```

### 4. Run Deployment Script
```bash
deploy_to_iis.bat
```

## Step 5: Configure IIS Application Pool

### 1. Create Application Pool
1. Open **IIS Manager**
2. Right-click **Application Pools** → **Add Application Pool**
3. Name: `DjangoAppPool`
4. .NET CLR Version: **No Managed Code**
5. Managed Pipeline Mode: **Integrated**

### 2. Configure Application Pool
1. Select **DjangoAppPool**
2. Set **Process Model** → **Identity** to **ApplicationPoolIdentity**
3. Set **Process Model** → **Idle Time-out** to **00:00:00** (disabled)

## Step 6: Create IIS Site

### 1. Create Site
1. Right-click **Sites** → **Add Website**
2. Site name: `ProjectManagerDashboard`
3. Physical path: `C:\inetpub\wwwroot\ProjectManagerDashboard`
4. Application pool: `DjangoAppPool`
5. Port: `80` (or your preferred port)

### 2. Configure Site Settings
1. Select your site
2. Double-click **Handler Mappings**
3. Verify **Python FastCGI** handler is present
4. If not, add it manually:
   - Request path: `*`
   - Module: `FastCgiModule`
   - Executable: `C:\Python39\python.exe|C:\Python39\Lib\site-packages\wfastcgi.py`

## Step 7: Configure Static Files

### 1. Set Permissions
```bash
# Give IIS_IUSRS read permissions to staticfiles and media folders
icacls "C:\inetpub\wwwroot\ProjectManagerDashboard\staticfiles" /grant "IIS_IUSRS:(OI)(CI)R"
icacls "C:\inetpub\wwwroot\ProjectManagerDashboard\media" /grant "IIS_IUSRS:(OI)(CI)R"
```

### 2. Configure URL Rewrite
The web.config already includes URL rewrite rules for static and media files.

## Step 8: SSL Configuration (Optional but Recommended)

### 1. Install SSL Certificate
1. Obtain SSL certificate from your CA
2. Install certificate in **Server Certificates**
3. Bind certificate to your site

### 2. Update Security Settings
Update your `.env` file:
```
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
SESSION_SECURE_COOKIES=True
SESSION_CSRF_COOKIE_SECURE=True
```

## Step 9: Test Deployment

### 1. Test Static Files
Visit: `http://your-domain.com/static/admin/css/base.css`

### 2. Test Django Application
Visit: `http://your-domain.com/`

### 3. Test Admin Panel
Visit: `http://your-domain.com/admin/`

## Troubleshooting

### Common Issues

1. **500 Internal Server Error**
   - Check IIS logs: `C:\inetpub\logs\LogFiles\`
   - Verify Python path in web.config
   - Check wfastcgi installation

2. **Static Files Not Loading**
   - Run `python manage.py collectstatic`
   - Check URL rewrite rules
   - Verify folder permissions

3. **Database Connection Error**
   - Check database credentials in `.env`
   - Verify MySQL service is running
   - Test connection with MySQL client

4. **Permission Denied**
   - Grant IIS_IUSRS permissions to project folder
   - Check Application Pool identity

### Log Files
- IIS Logs: `C:\inetpub\logs\LogFiles\`
- Django Logs: `C:\inetpub\wwwroot\ProjectManagerDashboard\logs\django.log`

## Performance Optimization

1. **Enable Compression**
   - In IIS Manager, select your site
   - Double-click **Compression**
   - Enable dynamic and static compression

2. **Configure Caching**
   - Set appropriate cache headers for static files
   - Configure browser caching

3. **Database Optimization**
   - Configure MySQL for production
   - Set appropriate buffer sizes
   - Enable query caching

## Security Considerations

1. **Remove Debug Mode**
   - Ensure `DEBUG=False` in production
   - Use environment variables for sensitive data

2. **Configure Firewall**
   - Allow only necessary ports
   - Block direct database access

3. **Regular Updates**
   - Keep Python and Django updated
   - Monitor security advisories
   - Regular security scans
