# Django Website Deployment Guide
## Domain: projecthelal.rcs.ir

This guide provides step-by-step instructions for deploying your Django Project Manager Dashboard using nginx and nssm on Windows Server.

## Prerequisites

- Windows Server 2016/2019/2022 or Windows 10/11
- Python 3.9+ installed
- MySQL Server installed and configured
- Administrator privileges
- Domain DNS pointing to your server IP

## Quick Deployment

1. **Run the deployment script as Administrator:**
   ```cmd
   deploy_website.bat
   ```

2. **Configure DNS:**
   - Point `projecthelal.rcs.ir` to your server's public IP
   - Point `www.projecthelal.rcs.ir` to your server's public IP

3. **Access your website:**
   - HTTP: http://projecthelal.rcs.ir
   - HTTPS: https://projecthelal.rcs.ir (after SSL setup)

## Scripts Overview

### 1. `deploy_website.bat` - Main Deployment Script
- Updates Django settings for production
- Installs Python dependencies
- Collects static files
- Runs database migrations
- Configures nginx with domain settings
- Installs nginx and Django as Windows services
- Starts all services
- Configures Windows Firewall

### 2. `manage_services.bat` - Service Management
- Start/stop/restart services
- Check service status
- View logs
- Test website connectivity

### 3. `setup_ssl.bat` - SSL Certificate Setup
- Let's Encrypt certificates (free)
- Existing certificate import
- Self-signed certificates (testing)

## Manual Configuration

### Environment Variables (.env file)
```env
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=projecthelal.rcs.ir,www.projecthelal.rcs.ir,localhost,127.0.0.1

# Database Configuration
DB_ENGINE=django.db.backends.mysql
DB_NAME=project_manager_db
DB_USER=root
DB_PASSWORD=your-mysql-password
DB_HOST=localhost
DB_PORT=3306

# Security Settings
SESSION_COOKIE_SECURE=False  # Set to True for HTTPS
SESSION_SECURE_COOKIES=False  # Set to True for HTTPS
SESSION_CSRF_COOKIE_SECURE=False  # Set to True for HTTPS
SECURE_SSL_REDIRECT=False  # Set to True for HTTPS
```

### Nginx Configuration
The deployment script automatically configures nginx with:
- Domain-specific server blocks
- Static file serving
- Media file serving
- Rate limiting
- Security headers
- Proxy pass to Django application

### Service Configuration
- **Nginx Service**: Serves static files and proxies requests
- **Django Service**: Runs the Django application on port 8000

## Service Management Commands

### Using the Management Script
```cmd
manage_services.bat
```

### Manual Service Commands
```cmd
# Start services
sc start nginx
sc start DjangoProjectManager

# Stop services
sc stop DjangoProjectManager
sc stop nginx

# Restart services
sc stop DjangoProjectManager && sc stop nginx
sc start nginx && sc start DjangoProjectManager

# Check status
sc query nginx
sc query DjangoProjectManager
```

## SSL Certificate Setup

### Option 1: Let's Encrypt (Recommended)
```cmd
setup_ssl.bat
# Choose option 1
```

### Option 2: Existing Certificates
```cmd
setup_ssl.bat
# Choose option 2
# Provide paths to your .crt and .key files
```

### Option 3: Self-Signed (Testing Only)
```cmd
setup_ssl.bat
# Choose option 3
```

## Log Files

### Nginx Logs
- Access: `nginx/logs/access.log`
- Error: `nginx/logs/error.log`
- Service Output: `nginx/logs/nginx_stdout.log`
- Service Error: `nginx/logs/nginx_stderr.log`

### Django Logs
- Application: `logs/django.log`
- Service Output: `logs/django_stdout.log`
- Service Error: `logs/django_stderr.log`

## Troubleshooting

### Common Issues

1. **Services won't start:**
   - Check if ports 80 and 8000 are available
   - Verify Python path in nssm configuration
   - Check log files for errors

2. **Website not accessible:**
   - Verify DNS configuration
   - Check Windows Firewall settings
   - Ensure services are running

3. **Static files not loading:**
   - Run `python manage.py collectstatic --noinput`
   - Check nginx configuration for static file paths

4. **Database connection errors:**
   - Verify MySQL service is running
   - Check database credentials in .env file
   - Ensure database exists

### Port Configuration
- **Port 80**: nginx (HTTP)
- **Port 443**: nginx (HTTPS)
- **Port 8000**: Django application (internal)

### Firewall Rules
The deployment script automatically adds:
- HTTP (Port 80)
- HTTPS (Port 443)

## Security Considerations

1. **Change default passwords** in .env file
2. **Use HTTPS** in production (run setup_ssl.bat)
3. **Regular updates** for Python packages and nginx
4. **Monitor logs** for suspicious activity
5. **Backup database** regularly

## Maintenance

### Regular Tasks
1. **Update dependencies:**
   ```cmd
   python -m pip install --upgrade -r requirements.txt
   ```

2. **Collect static files:**
   ```cmd
   python manage.py collectstatic --noinput
   ```

3. **Run migrations:**
   ```cmd
   python manage.py migrate
   ```

4. **Restart services:**
   ```cmd
   manage_services.bat
   # Choose option 3 (Restart all services)
   ```

### Backup
- Database: Export MySQL database
- Media files: Backup `media/` directory
- Static files: Backup `staticfiles/` directory
- Configuration: Backup `.env` and nginx config

## Support

For issues or questions:
1. Check log files first
2. Verify service status
3. Test connectivity
4. Review configuration files

## File Structure After Deployment

```
ProjectManagerDashboard/
├── deploy_website.bat          # Main deployment script
├── manage_services.bat         # Service management
├── setup_ssl.bat              # SSL certificate setup
├── .env                       # Environment variables
├── nginx/
│   ├── conf/nginx.conf        # Nginx configuration
│   ├── ssl/                   # SSL certificates (after SSL setup)
│   └── logs/                  # Nginx logs
├── logs/                      # Django logs
├── staticfiles/               # Collected static files
└── media/                     # User uploaded files
```

## URLs

- **Main Website**: http://projecthelal.rcs.ir
- **Admin Panel**: http://projecthelal.rcs.ir/admin/
- **API Endpoints**: http://projecthelal.rcs.ir/api/

After SSL setup:
- **Main Website**: https://projecthelal.rcs.ir
- **Admin Panel**: https://projecthelal.rcs.ir/admin/
- **API Endpoints**: https://projecthelal.rcs.ir/api/
