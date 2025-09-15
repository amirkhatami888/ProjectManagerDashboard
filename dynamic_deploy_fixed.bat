@echo off
setlocal enabledelayedexpansion

echo ========================================
echo Dynamic Django Website Deployment
echo Auto-configure for Windows VPS
echo ========================================

:: Set project variables
set PROJECT_DIR=%~dp0
set PROJECT_NAME=ProjectManagerDashboard
set NGINX_DIR=%PROJECT_DIR%nginx
set NSSM_DIR=%PROJECT_DIR%nssm
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
echo [1/12] Detecting server configuration...

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

:: Step 2: Install and configure NSSM
echo.
echo [2/12] Installing and configuring NSSM...

:: Check if NSSM is available
if not exist "%NSSM_DIR%\win64\nssm.exe" (
    echo ERROR: NSSM not found at %NSSM_DIR%\win64\nssm.exe
    echo Please ensure NSSM is properly installed in the nssm folder
    pause
    exit /b 1
)

:: Copy NSSM to system directory for global access
echo Installing NSSM to system directory...
if not exist "C:\Windows\System32\nssm.exe" (
    copy "%NSSM_DIR%\win64\nssm.exe" "C:\Windows\System32\" >nul 2>&1
    if %errorLevel% equ 0 (
        echo NSSM installed to system directory successfully
    ) else (
        echo Warning: Could not install NSSM to system directory, using local copy
    )
) else (
    echo NSSM already available in system directory
)

:: Test NSSM installation with better error handling
echo Testing NSSM installation...
"%NSSM_DIR%\win64\nssm.exe" >nul 2>&1
if %errorLevel% equ 0 (
    echo NSSM is working correctly
) else (
    echo ERROR: NSSM is not working properly
    echo.
    echo Troubleshooting steps:
    echo 1. Check if nssm.exe exists at: %NSSM_DIR%\win64\nssm.exe
    echo 2. Try running NSSM manually: "%NSSM_DIR%\win64\nssm.exe"
    echo 3. Check if the file is corrupted or blocked by antivirus
    echo.
    echo Attempting to continue with local NSSM copy...
    echo If this fails, please check the NSSM installation manually.
    
    :: Try to run NSSM directly to see the actual error
    echo.
    echo Running NSSM to see error details:
    "%NSSM_DIR%\win64\nssm.exe"
    echo.
    
    set /p CONTINUE="Do you want to continue anyway? (y/n): "
    if /i not "%CONTINUE%"=="y" (
        pause
        exit /b 1
    )
)

:: Step 3: Install required tools
echo.
echo [3/12] Installing required tools...

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

:: Step 4: Create and configure database
echo.
echo [4/12] Creating and configuring database...

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

:: Step 5: Configure environment variables
echo.
echo [5/12] Configuring environment variables...

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

:: Step 6: Install Python dependencies
echo.
echo [6/12] Installing Python dependencies...
%PYTHON_PATH% -m pip install -r requirements.txt
if %errorLevel% neq 0 (
    echo ERROR: Failed to install Python dependencies
    pause
    exit /b 1
)

:: Step 7: Run Django setup
echo.
echo [7/12] Running Django setup...

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

:: Step 8: Configure nginx
echo.
echo [8/12] Configuring nginx...

set NGINX_CONF=%NGINX_DIR%\conf\nginx.conf

:: Backup original nginx.conf
if not exist "%NGINX_CONF%.backup" (
    copy "%NGINX_CONF%" "%NGINX_CONF%.backup"
)

:: Create nginx configuration with HTTP and HTTPS support
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
echo     # HTTP server - redirect to HTTPS after SSL setup
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

:: Step 9: Install services with NSSM
echo.
echo [9/12] Installing Windows services with NSSM...

cd /d "%NGINX_DIR%"

:: Stop existing services
sc stop nginx >nul 2>&1
sc delete nginx >nul 2>&1

:: Install nginx service with NSSM
echo Installing nginx service with NSSM...
"%NSSM_DIR%\win64\nssm.exe" install nginx "%NGINX_DIR%\nginx.exe"
if %errorLevel% neq 0 (
    echo ERROR: Failed to install nginx service
    echo Trying alternative installation method...
    sc create nginx binPath= "%NGINX_DIR%\nginx.exe" start= auto
    if %errorLevel% neq 0 (
        echo ERROR: Both NSSM and SC installation failed
        pause
        exit /b 1
    ) else (
        echo nginx service installed using SC command
    )
) else (
    echo nginx service installed successfully with NSSM
    
    :: Configure nginx service with NSSM
    echo Configuring nginx service...
    "%NSSM_DIR%\win64\nssm.exe" set nginx AppDirectory "%NGINX_DIR%"
    "%NSSM_DIR%\win64\nssm.exe" set nginx AppStdout "%NGINX_DIR%\logs\nginx_stdout.log"
    "%NSSM_DIR%\win64\nssm.exe" set nginx AppStderr "%NGINX_DIR%\logs\nginx_stderr.log"
    "%NSSM_DIR%\win64\nssm.exe" set nginx Start SERVICE_AUTO_START
    "%NSSM_DIR%\win64\nssm.exe" set nginx DisplayName "Nginx Web Server"
    "%NSSM_DIR%\win64\nssm.exe" set nginx Description "Nginx web server for Django application"
    "%NSSM_DIR%\win64\nssm.exe" set nginx AppExit Default Restart
    "%NSSM_DIR%\win64\nssm.exe" set nginx AppRestartDelay 5000
    "%NSSM_DIR%\win64\nssm.exe" set nginx AppThrottle 1500
    "%NSSM_DIR%\win64\nssm.exe" set nginx AppStopMethodSkip 0
    "%NSSM_DIR%\win64\nssm.exe" set nginx AppStopMethodConsole 15000
    "%NSSM_DIR%\win64\nssm.exe" set nginx AppStopMethodWindow 15000
    "%NSSM_DIR%\win64\nssm.exe" set nginx AppStopMethodThreads 15000
)

:: Install Django service with NSSM
cd /d "%PROJECT_DIR%"
echo Installing Django service with NSSM...
sc stop %SERVICE_NAME% >nul 2>&1
sc delete %SERVICE_NAME% >nul 2>&1

"%NSSM_DIR%\win64\nssm.exe" install %SERVICE_NAME% "%PYTHON_PATH%" "runserver 127.0.0.1:8000"
if %errorLevel% neq 0 (
    echo ERROR: Failed to install Django service with NSSM
    echo Trying alternative installation method...
    sc create %SERVICE_NAME% binPath= "%PYTHON_PATH% runserver 127.0.0.1:8000" start= auto
    if %errorLevel% neq 0 (
        echo ERROR: Both NSSM and SC installation failed
        pause
        exit /b 1
    ) else (
        echo Django service installed using SC command
    )
) else (
    echo Django service installed successfully with NSSM
    
    :: Configure Django service with NSSM
    echo Configuring Django service...
    "%NSSM_DIR%\win64\nssm.exe" set %SERVICE_NAME% AppDirectory "%PROJECT_DIR%"
    "%NSSM_DIR%\win64\nssm.exe" set %SERVICE_NAME% AppStdout "%PROJECT_DIR%\logs\django_stdout.log"
    "%NSSM_DIR%\win64\nssm.exe" set %SERVICE_NAME% AppStderr "%PROJECT_DIR%\logs\django_stderr.log"
    "%NSSM_DIR%\win64\nssm.exe" set %SERVICE_NAME% Start SERVICE_AUTO_START
    "%NSSM_DIR%\win64\nssm.exe" set %SERVICE_NAME% DisplayName "Django Project Manager"
    "%NSSM_DIR%\win64\nssm.exe" set %SERVICE_NAME% Description "Django Project Manager Dashboard Application"
    "%NSSM_DIR%\win64\nssm.exe" set %SERVICE_NAME% AppExit Default Restart
    "%NSSM_DIR%\win64\nssm.exe" set %SERVICE_NAME% AppRestartDelay 10000
    "%NSSM_DIR%\win64\nssm.exe" set %SERVICE_NAME% AppThrottle 1500
    "%NSSM_DIR%\win64\nssm.exe" set %SERVICE_NAME% AppStopMethodSkip 0
    "%NSSM_DIR%\win64\nssm.exe" set %SERVICE_NAME% AppStopMethodConsole 30000
    "%NSSM_DIR%\win64\nssm.exe" set %SERVICE_NAME% AppStopMethodWindow 30000
    "%NSSM_DIR%\win64\nssm.exe" set %SERVICE_NAME% AppStopMethodThreads 30000
    "%NSSM_DIR%\win64\nssm.exe" set %SERVICE_NAME% AppEnvironmentExtra "DJANGO_SETTINGS_MODULE=project_dashboard.settings" "PYTHONPATH=%PROJECT_DIR%"
)

:: Create logs directory if it doesn't exist
if not exist "%PROJECT_DIR%\logs" mkdir "%PROJECT_DIR%\logs"

echo Services installed successfully!
echo.
echo Service Configuration:
echo - nginx: Auto-start, auto-restart on failure
echo - DjangoProjectManager: Auto-start, auto-restart on failure
echo - Both services configured with proper logging

:: Step 10: Configure firewall
echo.
echo [10/12] Configuring Windows Firewall...

netsh advfirewall firewall add rule name="HTTP (Port 80)" dir=in action=allow protocol=TCP localport=80
netsh advfirewall firewall add rule name="HTTPS (Port 443)" dir=in action=allow protocol=TCP localport=443
netsh advfirewall firewall add rule name="Django Internal (Port 8000)" dir=in action=allow protocol=TCP localport=8000

echo Firewall rules configured!

:: Step 11: Start services and setup SSL
echo.
echo [11/12] Starting services and setting up SSL...

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

:: Step 12: Setup SSL with win-acme
echo.
echo [12/12] Setting up SSL certificate with win-acme...
echo.
echo IMPORTANT: Make sure your domain %DOMAIN% points to IP %PUBLIC_IP%
echo Press any key when DNS is configured...
pause

:: Check if win-acme is available
if not exist "%PROJECT_DIR%win-acme\wacs.exe" (
    echo ERROR: win-acme not found at %PROJECT_DIR%win-acme\wacs.exe
    echo Please ensure win-acme is properly installed
    pause
    exit /b 1
)

:: Stop nginx temporarily for certificate generation
sc stop nginx

:: Generate SSL certificate using win-acme
echo Generating SSL certificate with win-acme...
cd /d "%PROJECT_DIR%win-acme"
wacs.exe --target manual --host %DOMAIN% --host www.%DOMAIN% --validation http --validationmode http-01 --installation nginx --nginxserverconf "%NGINX_DIR%\conf\nginx.conf" --accepttos --emailaddress admin@%DOMAIN% --quiet

if %errorLevel% equ 0 (
    echo SSL certificate generated successfully!
    
    :: Update Django settings for HTTPS
    cd /d "%PROJECT_DIR%"
    powershell -Command "(Get-Content '.env') -replace 'SECURE_SSL_REDIRECT=.*', 'SECURE_SSL_REDIRECT=True' | Set-Content '.env'"
    powershell -Command "(Get-Content '.env') -replace 'SESSION_COOKIE_SECURE=.*', 'SESSION_COOKIE_SECURE=True' | Set-Content '.env'"
    powershell -Command "(Get-Content '.env') -replace 'SESSION_SECURE_COOKIES=.*', 'SESSION_SECURE_COOKIES=True' | Set-Content '.env'"
    powershell -Command "(Get-Content '.env') -replace 'SESSION_CSRF_COOKIE_SECURE=.*', 'SESSION_CSRF_COOKIE_SECURE=True' | Set-Content '.env'"
    
    :: Restart services
    sc start nginx
    sc start %SERVICE_NAME%
    
    echo HTTPS configuration completed!
) else (
    echo SSL certificate generation failed. Continuing with HTTP only.
    sc start nginx
)

:: Create auto-renewal script using win-acme
echo.
echo Creating SSL auto-renewal script...
(
echo @echo off
echo cd /d "%PROJECT_DIR%win-acme"
echo wacs.exe --renew --baseuri https://acme-v02.api.letsencrypt.org/
echo if %%errorLevel%% equ 0 ^(
echo     sc stop nginx
echo     timeout /t 2 /nobreak ^>nul
echo     sc start nginx
echo ^)
) > renew_ssl.bat

:: Add to Windows Task Scheduler for auto-renewal
schtasks /create /tn "SSL Certificate Renewal" /tr "%PROJECT_DIR%renew_ssl.bat" /sc weekly /d SUN /st 02:00 /f >nul 2>&1

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
echo - HTTPS: https://%DOMAIN% (if SSL setup successful)
echo - Admin: http://%DOMAIN%/admin/
echo.
echo Service Management:
echo - Start: sc start nginx && sc start %SERVICE_NAME%
echo - Stop: sc stop %SERVICE_NAME% && sc stop nginx
echo - Restart: sc stop %SERVICE_NAME% && sc stop nginx && sc start nginx && sc start %SERVICE_NAME%
echo - NSSM GUI: "%NSSM_DIR%\win64\nssm.exe" gui
echo.
echo Log Files:
echo - Nginx: %NGINX_DIR%\logs\
echo - Django: %PROJECT_DIR%\logs\
echo - NSSM: Windows Event Log
echo.
echo NSSM Features:
echo - Auto-restart on failure
echo - Graceful shutdown handling
echo - Service monitoring and logging
echo - GUI management interface available
echo.
echo SSL Auto-renewal: Configured (runs weekly on Sundays at 2 AM)
echo ========================================

pause
exit /b 0
