# Django Website Batch Files Guide
## Complete Deployment and Server Management

This guide explains how to use all the batch files for deploying and managing your Django website on Windows VPS.

## 📋 Table of Contents

1. [Deployment Scripts](#deployment-scripts)
2. [Server Management Scripts](#server-management-scripts)
3. [SSL Management Scripts](#ssl-management-scripts)
4. [Service Management Scripts](#service-management-scripts)
5. [Quick Start Guide](#quick-start-guide)
6. [Troubleshooting](#troubleshooting)
7. [Advanced Usage](#advanced-usage)

## 🚀 Deployment Scripts

### 1. `dynamic_deploy.bat` - Main Deployment Script
**Purpose**: Complete automated deployment with win-acme SSL
**Usage**: `dynamic_deploy.bat`
**Requirements**: Administrator privileges

**What it does**:
- Auto-detects server IP addresses
- Creates MySQL database and user
- Configures Django settings
- Installs nginx and Django as Windows services using NSSM
- Sets up SSL certificates with win-acme
- Configures Windows Firewall
- Sets up automatic SSL renewal

**Steps**:
1. Run as Administrator
2. Enter your domain name when prompted
3. Enter MySQL root password
4. Choose whether to create Django superuser
5. Wait for DNS configuration (when prompted)
6. Script handles everything else automatically

### 2. `deploy_with_winacme.bat` - Enhanced Deployment Script
**Purpose**: Same as dynamic_deploy.bat but with enhanced win-acme integration
**Usage**: `deploy_with_winacme.bat`
**Requirements**: Administrator privileges

**Enhanced features**:
- Better win-acme integration
- More detailed SSL configuration
- Enhanced error handling
- Comprehensive logging

## 🎮 Server Management Scripts

### 3. `start_server.bat` - Start Server
**Purpose**: Start all website services
**Usage**: `start_server.bat`
**Requirements**: Administrator privileges

**What it does**:
- Starts nginx service
- Starts Django service
- Tests connectivity
- Shows service status
- Displays access URLs

### 4. `stop_server.bat` - Stop Server
**Purpose**: Stop all website services
**Usage**: `stop_server.bat`
**Requirements**: Administrator privileges

**What it does**:
- Stops Django service gracefully
- Stops nginx service
- Checks for running processes
- Kills any remaining processes
- Verifies ports are free
- Shows final status

### 5. `restart_server.bat` - Restart Server
**Purpose**: Restart all website services
**Usage**: `restart_server.bat`
**Requirements**: Administrator privileges

**What it does**:
- Stops all services
- Waits for complete shutdown
- Starts all services
- Tests connectivity
- Shows service status

## 🔒 SSL Management Scripts

### 6. `setup_ssl_winacme.bat` - SSL Certificate Management
**Purpose**: Manage SSL certificates with win-acme
**Usage**: `setup_ssl_winacme.bat`
**Requirements**: Administrator privileges

**Options**:
1. Create new SSL certificate
2. Renew existing certificate
3. List existing certificates
4. Test SSL configuration
5. Interactive win-acme setup

### 7. `configure_dns.bat` - DNS Configuration Helper
**Purpose**: Help configure DNS settings
**Usage**: `configure_dns.bat`
**Requirements**: None

**What it does**:
- Detects public IP address
- Provides DNS configuration instructions
- Tests DNS propagation
- Monitors DNS resolution status

## ⚙️ Service Management Scripts

### 8. `advanced_service_manager.bat` - Advanced Service Management
**Purpose**: Comprehensive service management and monitoring
**Usage**: `advanced_service_manager.bat`
**Requirements**: Administrator privileges

**Features**:
- Start/stop/restart services
- Real-time log monitoring
- Database management (backup/restore)
- SSL certificate management
- Website backup and restore
- Performance monitoring
- Security checks
- System updates

### 9. `nssm_manager.bat` - NSSM Service Manager
**Purpose**: Manage Windows services with NSSM
**Usage**: `nssm_manager.bat`
**Requirements**: Administrator privileges

**Features**:
- Open NSSM GUI
- Install/remove services
- Configure service parameters
- View service status and logs
- Start/stop/restart services

### 10. `manage_services.bat` - Basic Service Management
**Purpose**: Basic service management operations
**Usage**: `manage_services.bat`
**Requirements**: Administrator privileges

**Features**:
- Start/stop/restart services
- Check service status
- View service logs
- Test website connectivity

## 🚀 Quick Start Guide

### First-Time Deployment

1. **Prepare your server**:
   ```cmd
   # Ensure you have:
   # - Windows Server 2016/2019/2022 or Windows 10/11
   # - Python 3.9+ installed
   # - MySQL Server installed
   # - Domain name pointing to your server
   ```

2. **Run the deployment**:
   ```cmd
   # Right-click and "Run as administrator"
   dynamic_deploy.bat
   ```

3. **Follow the prompts**:
   - Enter your domain name
   - Enter MySQL root password
   - Choose whether to create superuser
   - Wait for DNS configuration

4. **Access your website**:
   - HTTP: `http://your-domain.com`
   - HTTPS: `https://your-domain.com` (after SSL setup)
   - Admin: `http://your-domain.com/admin/`

### Daily Operations

**Start the server**:
```cmd
start_server.bat
```

**Stop the server**:
```cmd
stop_server.bat
```

**Restart the server**:
```cmd
restart_server.bat
```

**Check server status**:
```cmd
advanced_service_manager.bat
# Choose option 4 (Check service status)
```

## 🔧 Troubleshooting

### Common Issues

#### 1. Services won't start
```cmd
# Check service status
sc query nginx
sc query DjangoProjectManager

# Check logs
type nginx\logs\error.log
type logs\django_stderr.log

# Restart services
restart_server.bat
```

#### 2. Website not accessible
```cmd
# Test connectivity
advanced_service_manager.bat
# Choose option 6 (Test website)

# Check firewall
netsh advfirewall show allprofiles

# Check ports
netstat -an | findstr ":80 "
netstat -an | findstr ":8000 "
```

#### 3. SSL certificate issues
```cmd
# Check certificate status
setup_ssl_winacme.bat
# Choose option 1 (Check certificate status)

# Renew certificate
setup_ssl_winacme.bat
# Choose option 2 (Renew certificate)
```

#### 4. Database connection errors
```cmd
# Test database connection
mysql -u django_user -pdjango_password_2024 project_manager_db

# Check MySQL service
sc query mysql
```

### Emergency Procedures

#### Complete server restart
```cmd
stop_server.bat
timeout /t 10 /nobreak >nul
start_server.bat
```

#### Force kill all processes
```cmd
taskkill /f /im nginx.exe
taskkill /f /im python.exe
```

#### Reset services
```cmd
nssm_manager.bat
# Remove services and reinstall
```

## 📊 Advanced Usage

### Service Monitoring

**Real-time log monitoring**:
```cmd
advanced_service_manager.bat
# Choose option 7 (Monitor real-time logs)
```

**Performance monitoring**:
```cmd
advanced_service_manager.bat
# Choose option 13 (Performance monitoring)
```

**Security checks**:
```cmd
advanced_service_manager.bat
# Choose option 14 (Security check)
```

### Backup and Recovery

**Create backup**:
```cmd
advanced_service_manager.bat
# Choose option 10 (Backup website)
```

**Restore from backup**:
```cmd
advanced_service_manager.bat
# Choose option 11 (Restore website)
```

### SSL Certificate Management

**Manual SSL operations**:
```cmd
# Open win-acme GUI
setup_ssl_winacme.bat
# Choose option 5 (Interactive setup)

# Or use command line
cd win-acme
wacs.exe --list
wacs.exe --renew
```

### Database Management

**Database operations**:
```cmd
advanced_service_manager.bat
# Choose option 8 (Database management)
```

**Manual database commands**:
```cmd
# Backup database
mysqldump -u django_user -pdjango_password_2024 project_manager_db > backup.sql

# Restore database
mysql -u django_user -pdjango_password_2024 project_manager_db < backup.sql
```

## 📁 File Structure

```
ProjectManagerDashboard/
├── dynamic_deploy.bat              # Main deployment script
├── deploy_with_winacme.bat        # Enhanced deployment with win-acme
├── start_server.bat               # Start all services
├── stop_server.bat                # Stop all services
├── restart_server.bat             # Restart all services
├── setup_ssl_winacme.bat          # SSL certificate management
├── configure_dns.bat              # DNS configuration helper
├── advanced_service_manager.bat   # Advanced service management
├── nssm_manager.bat               # NSSM service manager
├── manage_services.bat            # Basic service management
├── renew_ssl.bat                  # SSL auto-renewal script
├── .env                           # Environment variables
├── nginx/
│   ├── conf/nginx.conf            # Nginx configuration
│   └── logs/                      # Nginx logs
├── logs/                          # Django logs
├── staticfiles/                   # Collected static files
└── media/                         # User uploaded files
```

## 🔄 Service Lifecycle

### Automatic Startup
Services are configured to start automatically when Windows starts:
- nginx: Auto-start with 5s restart delay
- DjangoProjectManager: Auto-start with 10s restart delay

### Manual Control
```cmd
# Start services
start_server.bat

# Stop services
stop_server.bat

# Restart services
restart_server.bat
```

### Service Monitoring
- NSSM monitors service health
- Auto-restart on failure
- Logging to files and Windows Event Log
- GUI management available

## 📞 Support

### Log Files
- **Nginx**: `nginx/logs/`
- **Django**: `logs/`
- **Windows Event Log**: Use Event Viewer
- **NSSM**: Windows Event Log

### Service Status
```cmd
# Check all services
sc query nginx
sc query DjangoProjectManager

# Check ports
netstat -an | findstr ":80 "
netstat -an | findstr ":8000 "
```

### Emergency Contacts
- Check logs first
- Use advanced service manager for diagnostics
- Review this guide for troubleshooting steps

## 🎯 Best Practices

1. **Always run as Administrator** for service management
2. **Stop services before updates** to prevent conflicts
3. **Backup regularly** using the backup tools
4. **Monitor logs** for issues and performance
5. **Test SSL certificates** before they expire
6. **Keep services updated** using the update tools
7. **Use the GUI tools** for complex configurations

This comprehensive guide covers all aspects of deploying and managing your Django website using the provided batch files. Each script is designed to be user-friendly while providing powerful functionality for server management.
