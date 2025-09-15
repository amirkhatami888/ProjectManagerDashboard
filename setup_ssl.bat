@echo off
setlocal enabledelayedexpansion

echo ========================================
echo SSL Certificate Setup for projecthelal.rcs.ir
echo ========================================

:: Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This script must be run as Administrator
    echo Right-click and select "Run as administrator"
    pause
    exit /b 1
)

set DOMAIN=projecthelal.rcs.ir
set NGINX_DIR=%~dp0nginx
set CERT_DIR=%NGINX_DIR%\ssl

echo.
echo This script will help you set up SSL certificates for HTTPS.
echo.
echo Options:
echo 1. Use Let's Encrypt (Free SSL certificates)
echo 2. Use existing certificates
echo 3. Generate self-signed certificate (for testing)
echo 4. Exit
echo.
set /p ssl_choice="Enter your choice (1-4): "

if "%ssl_choice%"=="1" goto lets_encrypt
if "%ssl_choice%"=="2" goto existing_certs
if "%ssl_choice%"=="3" goto self_signed
if "%ssl_choice%"=="4" goto exit
echo Invalid choice.
goto exit

:lets_encrypt
echo.
echo Setting up Let's Encrypt SSL certificates...
echo.
echo NOTE: This requires:
echo 1. Domain pointing to this server
echo 2. Port 80 accessible from internet
echo 3. Certbot installed
echo.

:: Check if certbot is installed
certbot --version >nul 2>&1
if %errorLevel% neq 0 (
    echo Certbot is not installed. Please install it first:
    echo https://certbot.eff.org/instructions?ws=nginx&os=windows
    pause
    exit /b 1
)

:: Create certificate directory
if not exist "%CERT_DIR%" mkdir "%CERT_DIR%"

:: Stop nginx temporarily
sc stop nginx

:: Obtain certificate
certbot certonly --standalone -d %DOMAIN% -d www.%DOMAIN% --non-interactive --agree-tos --email admin@%DOMAIN%

if %errorLevel% equ 0 (
    echo Certificate obtained successfully!
    goto update_nginx_ssl
) else (
    echo Failed to obtain certificate. Please check your domain configuration.
    sc start nginx
    pause
    exit /b 1
)

:existing_certs
echo.
echo Using existing SSL certificates...
echo.
echo Please place your certificate files in: %CERT_DIR%
echo - Certificate file: %CERT_DIR%\%DOMAIN%.crt
echo - Private key file: %CERT_DIR%\%DOMAIN%.key
echo.
set /p cert_file="Enter path to certificate file (.crt): "
set /p key_file="Enter path to private key file (.key): "

if not exist "%cert_file%" (
    echo Certificate file not found: %cert_file%
    pause
    exit /b 1
)

if not exist "%key_file%" (
    echo Private key file not found: %key_file%
    pause
    exit /b 1
)

:: Create certificate directory
if not exist "%CERT_DIR%" mkdir "%CERT_DIR%"

:: Copy certificates
copy "%cert_file%" "%CERT_DIR%\%DOMAIN%.crt"
copy "%key_file%" "%CERT_DIR%\%DOMAIN%.key"

echo Certificates copied successfully!
goto update_nginx_ssl

:self_signed
echo.
echo Generating self-signed certificate (for testing only)...
echo.

:: Create certificate directory
if not exist "%CERT_DIR%" mkdir "%CERT_DIR%"

:: Generate self-signed certificate using OpenSSL
openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout "%CERT_DIR%\%DOMAIN%.key" -out "%CERT_DIR%\%DOMAIN%.crt" -subj "/C=IR/ST=Tehran/L=Tehran/O=Organization/CN=%DOMAIN%"

if %errorLevel% equ 0 (
    echo Self-signed certificate generated successfully!
    echo WARNING: This certificate will show security warnings in browsers.
) else (
    echo Failed to generate self-signed certificate.
    echo Please install OpenSSL or use existing certificates.
    pause
    exit /b 1
)

:update_nginx_ssl
echo.
echo Updating nginx configuration for HTTPS...

set NGINX_CONF=%NGINX_DIR%\conf\nginx.conf

:: Create HTTPS nginx configuration
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
echo     # HTTP server - redirect to HTTPS
echo     server {
echo         listen       80;
echo         server_name  %DOMAIN% www.%DOMAIN%;
echo         return 301 https://$server_name$request_uri;
echo     }
echo.
echo     # HTTPS server
echo     server {
echo         listen       443 ssl http2;
echo         server_name  %DOMAIN% www.%DOMAIN%;
echo         client_max_body_size 50M;
echo.
echo         # SSL configuration
echo         ssl_certificate      %CERT_DIR%\%DOMAIN%.crt;
echo         ssl_certificate_key  %CERT_DIR%\%DOMAIN%.key;
echo         ssl_session_cache    shared:SSL:1m;
echo         ssl_session_timeout  5m;
echo         ssl_ciphers  ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-SHA256:ECDHE-RSA-AES256-SHA384:ECDHE-RSA-AES128-SHA:ECDHE-RSA-AES256-SHA:DHE-RSA-AES128-SHA256:DHE-RSA-AES128-SHA:DHE-RSA-AES256-SHA256:DHE-RSA-AES256-SHA:ECDHE-RSA-DES-CBC3-SHA:EDH-RSA-DES-CBC3-SHA:AES128-GCM-SHA256:AES256-GCM-SHA384:AES128-SHA256:AES256-SHA256:AES128-SHA:AES256-SHA:DES-CBC3-SHA:HIGH:!aNULL:!eNULL:!EXPORT:!DES:!MD5:!PSK:!RC4;
echo         ssl_prefer_server_ciphers  on;
echo.
echo         # Security headers
echo         add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
echo         add_header X-Frame-Options "SAMEORIGIN" always;
echo         add_header X-Content-Type-Options "nosniff" always;
echo         add_header X-XSS-Protection "1; mode=block" always;
echo         add_header Referrer-Policy "strict-origin-when-cross-origin" always;
echo.
echo         # Static files
echo         location /static/ {
echo             alias %~dp0staticfiles/;
echo             expires 1y;
echo             add_header Cache-Control "public, immutable";
echo         }
echo.
echo         # Media files
echo         location /media/ {
echo             alias %~dp0media/;
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

:: Update Django settings for HTTPS
echo.
echo Updating Django settings for HTTPS...
powershell -Command "(Get-Content '.env') -replace 'SECURE_SSL_REDIRECT=.*', 'SECURE_SSL_REDIRECT=True' | Set-Content '.env'"
powershell -Command "(Get-Content '.env') -replace 'SESSION_COOKIE_SECURE=.*', 'SESSION_COOKIE_SECURE=True' | Set-Content '.env'"
powershell -Command "(Get-Content '.env') -replace 'SESSION_SECURE_COOKIES=.*', 'SESSION_SECURE_COOKIES=True' | Set-Content '.env'"
powershell -Command "(Get-Content '.env') -replace 'SESSION_CSRF_COOKIE_SECURE=.*', 'SESSION_CSRF_COOKIE_SECURE=True' | Set-Content '.env'"

:: Add HTTPS port to firewall
netsh advfirewall firewall add rule name="HTTPS (Port 443)" dir=in action=allow protocol=TCP localport=443

:: Restart services
echo.
echo Restarting services...
sc stop DjangoProjectManager
sc stop nginx
timeout /t 3 /nobreak >nul
sc start nginx
sc start DjangoProjectManager

echo.
echo ========================================
echo SSL SETUP COMPLETED!
echo ========================================
echo.
echo Your website is now available at:
echo https://%DOMAIN%
echo.
echo Certificate location: %CERT_DIR%
echo.
echo For Let's Encrypt certificates, set up auto-renewal:
echo certbot renew --quiet
echo.
echo ========================================

:exit
pause
