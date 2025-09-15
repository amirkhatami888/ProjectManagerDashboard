@echo off
echo ========================================
echo Create .env File for Django
echo ========================================

echo.
echo This script will create the .env file with correct database settings.
echo.

set /p CONFIRM="Do you want to create the .env file? (y/n): "
if /i not "%CONFIRM%"=="y" (
    echo Operation cancelled.
    pause
    exit /b 0
)

echo.
echo [1/3] Getting configuration details...

:: Get domain from user or use default
set /p DOMAIN="Enter your domain name (e.g., projecthelal.rcs.ir): "
if "%DOMAIN%"=="" set DOMAIN=projecthelal.rcs.ir

:: Get public IP
echo Getting public IP address...
curl -s --max-time 10 https://api.ipify.org > temp_ip.txt 2>nul
if exist temp_ip.txt (
    set /p PUBLIC_IP=<temp_ip.txt
    del temp_ip.txt
) else (
    set PUBLIC_IP=127.0.0.1
)

echo Domain: %DOMAIN%
echo Public IP: %PUBLIC_IP%

echo.
echo [2/3] Generating secret key...

:: Generate secret key
for /f %%i in ('python -c "import secrets; print(secrets.token_urlsafe(50))"') do set SECRET_KEY=%%i

echo Secret key generated: %SECRET_KEY%

echo.
echo [3/3] Creating .env file...

:: Create .env file with proper formatting
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
echo # Email Settings ^(Optional^)
echo EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
echo EMAIL_HOST=smtp.gmail.com
echo EMAIL_PORT=587
echo EMAIL_USE_TLS=True
echo EMAIL_HOST_USER=
echo EMAIL_HOST_PASSWORD=
) > .env

if exist ".env" (
    echo ✓ .env file created successfully
    echo.
    echo .env file contents:
    echo ========================================
    type .env
    echo ========================================
) else (
    echo ERROR: Failed to create .env file
    pause
    exit /b 1
)

echo.
echo ========================================
echo .env File Creation Complete!
echo ========================================
echo.
echo The .env file has been created with the following settings:
echo - Database: project_manager_db
echo - User: django_user
echo - Password: django_password_2024
echo - Domain: %DOMAIN%
echo - Public IP: %PUBLIC_IP%
echo.
echo You can now test Django database connection:
echo python manage.py check --database default
echo.
echo Or run the deployment script:
echo dynamic_deploy_clean.bat
echo.
pause
exit /b 0
