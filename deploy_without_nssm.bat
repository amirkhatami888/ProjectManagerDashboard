@echo off
setlocal enabledelayedexpansion

echo ========================================
echo Django Website Deployment (Without NSSM)
echo Using Windows SC Command for Services
echo ========================================

:: Set project variables
set PROJECT_DIR=%~dp0
set PROJECT_NAME=ProjectManagerDashboard
set NGINX_DIR=%PROJECT_DIR%nginx
set PYTHON_PATH=C:\Python39\python.exe
set PYTHON_SCRIPT=%PROJECT_DIR%manage.py
set SERVICE_NAME=DjangoProjectManager

:: Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This script must be run as Administrator
    echo Right-click and select "Run as administrator"
    pause
    exit /b 1
)

:: Step 1: Detect server IP and configure domain
echo.
echo [1/10] Detecting server configuration...

:: Get public IP address
echo Detecting public IP address...
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4 Address"') do (
    set LOCAL_IP=%%a
    set LOCAL_IP=!LOCAL_IP: =!
)

:: Try to get public IP from external service
echo Getting public IP address...
curl -s --max-time 10 https://api.ipify.org > temp_ip.txt 2>nul
if exist temp_ip.txt (
    set /p PUBLIC_IP=<temp_ip.txt
    del temp_ip.txt
) else (
    set PUBLIC_IP=%LOCAL_IP%
)

echo Local IP: %LOCAL_IP%
echo Public IP: %PUBLIC_IP%

:: Get domain from user or use default
echo.
set /p DOMAIN="Enter your domain name (e.g., projecthelal.rcs.ir): "
if "%DOMAIN%"=="" set DOMAIN=projecthelal.rcs.ir

echo Using domain: %DOMAIN%

:: Step 2: Install required tools
echo.
echo [2/10] Installing required tools...

:: Check if Python is installed
%PYTHON_PATH% --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Python 3.9+ is required but not found at %PYTHON_PATH%
    echo Please install Python 3.9+ and update the PYTHON_PATH variable
    pause
    exit /b 1
)

:: Install required Python packages
echo Installing Python packages...
%PYTHON_PATH% -m pip install --upgrade pip
%PYTHON_PATH% -m pip install mysql-connector-python

:: Check if MySQL is installed
mysql --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: MySQL is not installed or not in PATH
    echo Please install MySQL Server and add it to PATH
    pause
    exit /b 1
)

:: Step 3: Create and configure database
echo.
echo [3/10] Creating and configuring database...

:: Get MySQL root password
set /p MYSQL_ROOT_PASSWORD="Enter MySQL root password: "
if "%MYSQL_ROOT_PASSWORD%"=="" (
    echo ERROR: MySQL root password is required
    pause
    exit /b 1
)

:: Create database and user
echo Creating database and user...
mysql -u root -p%MYSQL_ROOT_PASSWORD% -e "CREATE DATABASE IF NOT EXISTS project_manager_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" 2>nul
mysql -u root -p%MYSQL_ROOT_PASSWORD% -e "CREATE USER IF NOT EXISTS 'django_user'@'localhost' IDENTIFIED BY 'django_password_2024';" 2>nul
mysql -u root -p%MYSQL_ROOT_PASSWORD% -e "GRANT ALL PRIVILEGES ON project_manager_db.* TO 'django_user'@'localhost';" 2>nul
mysql -u root -p%MYSQL_ROOT_PASSWORD% -e "FLUSH PRIVILEGES;" 2>nul

if %errorLevel% neq 0 (
    echo ERROR: Failed to create database or user
    pause
    exit /b 1
)

echo Database created successfully!

:: Step 4: Configure environment variables
echo.
echo [4/10] Configuring environment variables...

:: Generate secret key
for /f %%i in ('%PYTHON_PATH% -c "import secrets; print(secrets.token_urlsafe(50))"') do set SECRET_KEY=%%i

:: Create .env file
(
echo # Django Settings
echo SECRET_KEY=%SECRET_KEY%
echo DEBUG=False
echo ALLOWED_HOSTS=%DOMAIN%,www.%DOMAIN%,localhost,127.0.0.1,%PUBLIC_IP%
echo.
echo # Database Configuration
echo DB_ENGINE=django.db.backends.mysql
echo DB_NAME=project_manager_db
echo DB_USER=django_user
echo DB_PASSWORD=django_password_2024
echo DB_HOST=localhost
echo DB_PORT=3306
echo.
echo # Security Settings
echo SESSION_COOKIE_SECURE=False
echo SESSION_SECURE_COOKIES=False
echo SESSION_CSRF_COOKIE_SECURE=False
echo SECURE_SSL_REDIRECT=False
echo.
echo # Email Settings (Optional)
echo EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
echo EMAIL_HOST=smtp.gmail.com
echo EMAIL_PORT=587
echo EMAIL_USE_TLS=True
echo EMAIL_HOST_USER=
echo EMAIL_HOST_PASSWORD=
) > .env

echo Environment configuration created!

:: Step 5: Install Python dependencies
echo.
echo [5/10] Installing Python dependencies...
%PYTHON_PATH% -m pip install -r requirements.txt
if %errorLevel% neq 0 (
    echo ERROR: Failed to install Python dependencies
    pause
    exit /b 1
)

:: Step 6: Run Django setup
echo.
echo [6/10] Running Django setup...

:: Collect static files
%PYTHON_PATH% %PYTHON_SCRIPT% collectstatic --noinput
if %errorLevel% neq 0 (
    echo ERROR: Failed to collect static files
    pause
    exit /b 1
)

:: Run migrations
%PYTHON_PATH% %PYTHON_SCRIPT% migrate
if %errorLevel% neq 0 (
    echo ERROR: Failed to run database migrations
    pause
    exit /b 1
)

:: Create superuser (optional)
echo.
set /p CREATE_SUPERUSER="Create Django superuser? (y/n): "
if /i "%CREATE_SUPERUSER%"=="y" (
    echo Creating superuser...
    %PYTHON_PATH% %PYTHON_SCRIPT% createsuperuser --noinput --username admin --email admin@%DOMAIN% 2>nul
    if %errorLevel% equ 0 (
        echo Superuser created with username: admin
        echo Default password: admin123 (change this after first login)
        mysql -u root -p%MYSQL_ROOT_PASSWORD% -e "UPDATE project_manager_db.auth_user SET password='pbkdf2_sha256\$600000\$dummy\$dummy' WHERE username='admin';" 2>nul
    )
)

:: Step 7: Configure nginx
echo.
echo [7/10] Configuring nginx...

set NGINX_CONF=%NGINX_DIR%\conf\nginx.conf

:: Backup original nginx.conf
if not exist "%NGINX_CONF%.backup" (
    copy "%NGINX_CONF%" "%NGINX_CONF%.backup"
)

:: Create nginx configuration
(
echo #user  nobody;
echo worker_processes  1;
echo.
echo #error_log  logs/error.log;
echo #error_log  logs/error.log  notice;
echo #error_log  logs/error.log  info;
echo.
echo #pid        logs/nginx.pid;
echo.
echo.
echo events {
echo     worker_connections  1024;
echo }
echo.
echo.
echo http {
echo     include       mime.types;
echo     default_type  application/octet-stream;
echo.
echo     log_format  main  '$remote_addr - $remote_user [$time_local] "$request" '
echo                       '$status $body_bytes_sent "$http_referer" '
echo                       '"$http_user_agent" "$http_x_forwarded_for"';
echo.
echo     access_log  logs/access.log  main;
echo     error_log   logs/error.log;
echo.
echo     sendfile        on;
echo     tcp_nopush     on;
echo     tcp_nodelay    on;
echo.
echo     keepalive_timeout  65;
echo     types_hash_max_size 2048;
echo.
echo     gzip  on;
echo     gzip_vary on;
echo     gzip_min_length 1024;
echo     gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
echo.
echo     # Rate limiting
echo     limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;
echo     limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
echo.
echo     # Upstream for Django application
echo     upstream django_app {
echo         server 127.0.0.1:8000;
echo     }
echo.
echo     # HTTP server
echo     server {
echo         listen       80;
echo         server_name  %DOMAIN% www.%DOMAIN%;
echo         client_max_body_size 50M;
echo.
echo         # Security headers
echo         add_header X-Frame-Options "SAMEORIGIN" always;
echo         add_header X-Content-Type-Options "nosniff" always;
echo         add_header X-XSS-Protection "1; mode=block" always;
echo         add_header Referrer-Policy "strict-origin-when-cross-origin" always;
echo.
echo         # Let's Encrypt challenge
echo         location /.well-known/acme-challenge/ {
echo             root %NGINX_DIR%\html;
echo         }
echo.
echo         # Static files
echo         location /static/ {
echo             alias %PROJECT_DIR%staticfiles/;
echo             expires 1y;
echo             add_header Cache-Control "public, immutable";
echo         }
echo.
echo         # Media files
echo         location /media/ {
echo             alias %PROJECT_DIR%media/;
echo             expires 1M;
echo             add_header Cache-Control "public";
echo         }
echo.
echo         # Rate limiting for login
echo         location /accounts/login/ {
echo             limit_req zone=login burst=3 nodelay;
echo             proxy_pass http://django_app;
echo             proxy_set_header Host $host;
echo             proxy_set_header X-Real-IP $remote_addr;
echo             proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
echo             proxy_set_header X-Forwarded-Proto $scheme;
echo         }
echo.
echo         # Rate limiting for API endpoints
echo         location /api/ {
echo             limit_req zone=api burst=20 nodelay;
echo             proxy_pass http://django_app;
echo             proxy_set_header Host $host;
echo             proxy_set_header X-Real-IP $remote_addr;
echo             proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
echo             proxy_set_header X-Forwarded-Proto $scheme;
echo         }
echo.
echo         # Main application
echo         location / {
echo             proxy_pass http://django_app;
echo             proxy_set_header Host $host;
echo             proxy_set_header X-Real-IP $remote_addr;
echo             proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
echo             proxy_set_header X-Forwarded-Proto $scheme;
echo             proxy_connect_timeout 60s;
echo             proxy_send_timeout 60s;
echo             proxy_read_timeout 60s;
echo         }
echo.
echo         # Error pages
echo         error_page   500 502 503 504  /50x.html;
echo         location = /50x.html {
echo             root   html;
echo         }
echo     }
echo }
) > "%NGINX_CONF%"

echo Nginx configuration created!

:: Step 8: Install services with SC command
echo.
echo [8/10] Installing Windows services with SC command...

cd /d "%NGINX_DIR%"

:: Stop existing services
sc stop nginx >nul 2>&1
sc delete nginx >nul 2>&1

:: Install nginx service
echo Installing nginx service...
sc create nginx binPath= "%NGINX_DIR%\nginx.exe" start= auto DisplayName= "Nginx Web Server"
if %errorLevel% neq 0 (
    echo ERROR: Failed to install nginx service
    pause
    exit /b 1
)

:: Install Django service
cd /d "%PROJECT_DIR%"
echo Installing Django service...
sc stop %SERVICE_NAME% >nul 2>&1
sc delete %SERVICE_NAME% >nul 2>&1

sc create %SERVICE_NAME% binPath= "%PYTHON_PATH% runserver 127.0.0.1:8000" start= auto DisplayName= "Django Project Manager"
if %errorLevel% neq 0 (
    echo ERROR: Failed to install Django service
    pause
    exit /b 1
)

:: Create logs directory if it doesn't exist
if not exist "%PROJECT_DIR%\logs" mkdir "%PROJECT_DIR%\logs"

echo Services installed successfully with SC command!
echo.
echo Note: Services installed with SC command have basic functionality.
echo For advanced features like auto-restart, consider fixing NSSM issues.

:: Step 9: Configure firewall
echo.
echo [9/10] Configuring Windows Firewall...

netsh advfirewall firewall add rule name="HTTP (Port 80)" dir=in action=allow protocol=TCP localport=80
netsh advfirewall firewall add rule name="HTTPS (Port 443)" dir=in action=allow protocol=TCP localport=443
netsh advfirewall firewall add rule name="Django Internal (Port 8000)" dir=in action=allow protocol=TCP localport=8000

echo Firewall rules configured!

:: Step 10: Start services
echo.
echo [10/10] Starting services...

:: Start services
sc start nginx
sc start %SERVICE_NAME%

:: Wait for services to start
timeout /t 5 /nobreak >nul

:: Check if services are running
sc query nginx | find "RUNNING" >nul
if %errorLevel% neq 0 (
    echo ERROR: Nginx service failed to start
    pause
    exit /b 1
)

sc query %SERVICE_NAME% | find "RUNNING" >nul
if %errorLevel% neq 0 (
    echo ERROR: Django service failed to start
    pause
    exit /b 1
)

echo Services started successfully!

:: Final status check
echo.
echo ========================================
echo DEPLOYMENT COMPLETED SUCCESSFULLY!
echo ========================================
echo.
echo Server Information:
echo - Domain: %DOMAIN%
echo - Public IP: %PUBLIC_IP%
echo - Local IP: %LOCAL_IP%
echo.
echo Database Information:
echo - Database: project_manager_db
echo - User: django_user
echo - Password: django_password_2024
echo.
echo Website URLs:
echo - HTTP: http://%DOMAIN%
echo - Admin: http://%DOMAIN%/admin/
echo.
echo Service Management:
echo - Start: sc start nginx && sc start %SERVICE_NAME%
echo - Stop: sc stop %SERVICE_NAME% && sc stop nginx
echo - Restart: sc stop %SERVICE_NAME% && sc stop nginx && sc start nginx && sc start %SERVICE_NAME%
echo.
echo Log Files:
echo - Nginx: %NGINX_DIR%\logs\
echo - Django: %PROJECT_DIR%\logs\
echo.
echo Note: Services installed with SC command (basic functionality)
echo For advanced features, fix NSSM issues and re-run deployment.
echo ========================================

pause
exit /b 0
