@echo off
setlocal enabledelayedexpansion

echo ========================================
echo Django Website Deployment Script
echo Domain: projecthelal.rcs.ir
echo ========================================

:: Set project variables
set PROJECT_DIR=%~dp0
set PROJECT_NAME=ProjectManagerDashboard
set DOMAIN=projecthelal.rcs.ir
set NGINX_DIR=%PROJECT_DIR%nginx
set NSSM_DIR=%PROJECT_DIR%nssm
set PYTHON_PATH=C:\Python39\python.exe
set PYTHON_SCRIPT=%PROJECT_DIR%manage.py
set SERVICE_NAME=DjangoProjectManager

echo Project Directory: %PROJECT_DIR%
echo Domain: %DOMAIN%

:: Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This script must be run as Administrator
    echo Right-click and select "Run as administrator"
    pause
    exit /b 1
)

:: Step 1: Update Django settings for production
echo.
echo [1/8] Updating Django settings for production...
if not exist ".env" (
    echo Creating .env file from template...
    copy "env.example" ".env"
)

:: Update .env file with production settings
powershell -Command "(Get-Content '.env') -replace 'ALLOWED_HOSTS=.*', 'ALLOWED_HOSTS=%DOMAIN%,www.%DOMAIN%,localhost,127.0.0.1' | Set-Content '.env'"
powershell -Command "(Get-Content '.env') -replace 'DEBUG=.*', 'DEBUG=False' | Set-Content '.env'"

:: Update settings.py ALLOWED_HOSTS
powershell -Command "(Get-Content 'project_dashboard\settings.py') -replace 'ALLOWED_HOSTS = config.*', 'ALLOWED_HOSTS = config(''ALLOWED_HOSTS'', default=''%DOMAIN%,www.%DOMAIN%,localhost,127.0.0.1'').split('','')' | Set-Content 'project_dashboard\settings.py'"

echo Django settings updated for domain: %DOMAIN%

:: Step 2: Install Python dependencies
echo.
echo [2/8] Installing Python dependencies...
%PYTHON_PATH% -m pip install --upgrade pip
%PYTHON_PATH% -m pip install -r requirements.txt
if %errorLevel% neq 0 (
    echo ERROR: Failed to install Python dependencies
    pause
    exit /b 1
)

:: Step 3: Collect static files
echo.
echo [3/8] Collecting static files...
%PYTHON_PATH% %PYTHON_SCRIPT% collectstatic --noinput
if %errorLevel% neq 0 (
    echo ERROR: Failed to collect static files
    pause
    exit /b 1
)

:: Step 4: Run database migrations
echo.
echo [4/8] Running database migrations...
%PYTHON_PATH% %PYTHON_SCRIPT% migrate
if %errorLevel% neq 0 (
    echo ERROR: Failed to run database migrations
    pause
    exit /b 1
)

:: Step 5: Create nginx configuration
echo.
echo [5/8] Creating nginx configuration...
set NGINX_CONF=%NGINX_DIR%\conf\nginx.conf

:: Backup original nginx.conf
if not exist "%NGINX_CONF%.backup" (
    copy "%NGINX_CONF%" "%NGINX_CONF%.backup"
)

:: Create new nginx configuration
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

echo Nginx configuration created for domain: %DOMAIN%

:: Step 6: Install and configure nginx service
echo.
echo [6/8] Installing nginx service...
cd /d "%NGINX_DIR%"

:: Stop existing nginx service if running
sc stop nginx >nul 2>&1
sc delete nginx >nul 2>&1

:: Install nginx as Windows service using nssm
"%NSSM_DIR%\win64\nssm.exe" install nginx "%NGINX_DIR%\nginx.exe"
if %errorLevel% neq 0 (
    echo ERROR: Failed to install nginx service
    pause
    exit /b 1
)

:: Configure nginx service
"%NSSM_DIR%\win64\nssm.exe" set nginx AppDirectory "%NGINX_DIR%"
"%NSSM_DIR%\win64\nssm.exe" set nginx AppStdout "%NGINX_DIR%\logs\nginx_stdout.log"
"%NSSM_DIR%\win64\nssm.exe" set nginx AppStderr "%NGINX_DIR%\logs\nginx_stderr.log"
"%NSSM_DIR%\win64\nssm.exe" set nginx Start SERVICE_AUTO_START

echo Nginx service installed and configured

:: Step 7: Install and configure Django service
echo.
echo [7/8] Installing Django application service...
cd /d "%PROJECT_DIR%"

:: Stop existing Django service if running
sc stop %SERVICE_NAME% >nul 2>&1
sc delete %SERVICE_NAME% >nul 2>&1

:: Install Django as Windows service using nssm
"%NSSM_DIR%\win64\nssm.exe" install %SERVICE_NAME% "%PYTHON_PATH%" "runserver 127.0.0.1:8000"
if %errorLevel% neq 0 (
    echo ERROR: Failed to install Django service
    pause
    exit /b 1
)

:: Configure Django service
"%NSSM_DIR%\win64\nssm.exe" set %SERVICE_NAME% AppDirectory "%PROJECT_DIR%"
"%NSSM_DIR%\win64\nssm.exe" set %SERVICE_NAME% AppStdout "%PROJECT_DIR%\logs\django_stdout.log"
"%NSSM_DIR%\win64\nssm.exe" set %SERVICE_NAME% AppStderr "%PROJECT_DIR%\logs\django_stderr.log"
"%NSSM_DIR%\win64\nssm.exe" set %SERVICE_NAME% Start SERVICE_AUTO_START

:: Set environment variables for Django service
"%NSSM_DIR%\win64\nssm.exe" set %SERVICE_NAME% AppEnvironmentExtra "DJANGO_SETTINGS_MODULE=project_dashboard.settings" "PYTHONPATH=%PROJECT_DIR%"

echo Django service installed and configured

:: Step 8: Start services
echo.
echo [8/8] Starting services...
sc start nginx
if %errorLevel% neq 0 (
    echo ERROR: Failed to start nginx service
    pause
    exit /b 1
)

sc start %SERVICE_NAME%
if %errorLevel% neq 0 (
    echo ERROR: Failed to start Django service
    pause
    exit /b 1
)

:: Wait for services to start
timeout /t 5 /nobreak >nul

:: Check service status
echo.
echo Checking service status...
sc query nginx | find "RUNNING" >nul
if %errorLevel% equ 0 (
    echo ✓ Nginx service is running
) else (
    echo ✗ Nginx service failed to start
)

sc query %SERVICE_NAME% | find "RUNNING" >nul
if %errorLevel% equ 0 (
    echo ✓ Django service is running
) else (
    echo ✗ Django service failed to start
)

:: Create firewall rules
echo.
echo Configuring Windows Firewall...
netsh advfirewall firewall add rule name="HTTP (Port 80)" dir=in action=allow protocol=TCP localport=80
netsh advfirewall firewall add rule name="HTTPS (Port 443)" dir=in action=allow protocol=TCP localport=443

:: Create DNS configuration reminder
echo.
echo ========================================
echo DEPLOYMENT COMPLETED SUCCESSFULLY!
echo ========================================
echo.
echo IMPORTANT: DNS Configuration Required
echo ========================================
echo Please configure your DNS settings to point %DOMAIN% to this server's IP address:
echo.
echo A Record: %DOMAIN% → [YOUR_SERVER_IP]
echo A Record: www.%DOMAIN% → [YOUR_SERVER_IP]
echo.
echo Services Status:
echo - Nginx: http://%DOMAIN% (Port 80)
echo - Django: http://127.0.0.1:8000 (Internal)
echo.
echo Log Files:
echo - Nginx: %NGINX_DIR%\logs\
echo - Django: %PROJECT_DIR%\logs\
echo.
echo Service Management:
echo - Start: sc start nginx && sc start %SERVICE_NAME%
echo - Stop: sc stop nginx && sc stop %SERVICE_NAME%
echo - Restart: sc stop nginx && sc stop %SERVICE_NAME% && sc start nginx && sc start %SERVICE_NAME%
echo.
echo Website URL: http://%DOMAIN%
echo ========================================

pause
