@echo off
echo ========================================
echo Django Database Configuration Fix
echo ========================================

echo.
echo This script will fix Django database connection issues.
echo.

set /p CONFIRM="Do you want to fix Django database configuration? (y/n): "
if /i not "%CONFIRM%"=="y" (
    echo Operation cancelled.
    pause
    exit /b 0
)

echo.
echo [1/4] Checking current configuration...

:: Check if .env file exists
if exist ".env" (
    echo ✓ .env file exists
    echo Current .env contents:
    type .env
    echo.
) else (
    echo ✗ .env file not found
    echo This is the cause of the database connection issue
)

echo.
echo [2/4] Getting MySQL root password...

set /p MYSQL_ROOT_PASSWORD="Enter MySQL root password: "
if "%MYSQL_ROOT_PASSWORD%"=="" (
    echo ERROR: MySQL root password is required
    pause
    exit /b 1
)

echo.
echo [3/4] Creating .env file with correct database settings...

:: Get domain from user or use default
set /p DOMAIN="Enter your domain name (e.g., projecthelal.rcs.ir): "
if "%DOMAIN%"=="" set DOMAIN=projecthelal.rcs.ir

:: Get public IP
curl -s --max-time 10 https://api.ipify.org > temp_ip.txt 2>nul
if exist temp_ip.txt (
    set /p PUBLIC_IP=<temp_ip.txt
    del temp_ip.txt
) else (
    set PUBLIC_IP=127.0.0.1
)

:: Generate secret key
for /f %%i in ('python -c "import secrets; print(secrets.token_urlsafe(50))"') do set SECRET_KEY=%%i

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

echo ✓ .env file created successfully

echo.
echo [4/4] Testing Django database connection...

:: Test Django database connection
python manage.py check --database default
if %errorLevel% neq 0 (
    echo ERROR: Django database connection test failed
    echo.
    echo Troubleshooting steps:
    echo 1. Make sure MySQL is running
    echo 2. Verify the root password is correct
    echo 3. Check if the database and user exist
    echo.
    echo You can run these commands to check:
    echo mysql -u root -p%MYSQL_ROOT_PASSWORD% -e "SHOW DATABASES;"
    echo mysql -u root -p%MYSQL_ROOT_PASSWORD% -e "SELECT User, Host FROM mysql.user WHERE User='django_user';"
    pause
    exit /b 1
)

echo ✓ Django database connection test successful

echo.
echo ========================================
echo Database Configuration Fix Complete!
echo ========================================
echo.
echo Django is now configured to connect to MySQL.
echo.
echo Database Information:
echo - Database: project_manager_db
echo - User: django_user
echo - Password: django_password_2024
echo.
echo You can now run:
echo python manage.py migrate
echo python manage.py collectstatic --noinput
echo.
echo Or continue with the deployment script:
echo dynamic_deploy_clean.bat
echo.
pause
exit /b 0
