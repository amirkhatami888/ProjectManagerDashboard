@echo off
echo ========================================
echo Start Services Manually
echo ========================================

echo.
echo This script will start the services manually if they're not running.
echo.

echo [1/4] Checking current service status...

:: Check Nginx service
sc query nginx | find "RUNNING" >nul
if %errorLevel% equ 0 (
    echo ✓ Nginx service is already running
    set NGINX_RUNNING=1
) else (
    echo ✗ Nginx service is not running
    set NGINX_RUNNING=0
)

:: Check Django service
sc query DjangoProjectManager | find "RUNNING" >nul
if %errorLevel% equ 0 (
    echo ✓ Django service is already running
    set DJANGO_RUNNING=1
) else (
    echo ✗ Django service is not running
    set DJANGO_RUNNING=0
)

echo.

echo [2/4] Starting Nginx service...

if %NGINX_RUNNING% equ 0 (
    echo Starting Nginx service...
    sc start nginx
    timeout /t 5 /nobreak >nul
    
    :: Check if Nginx started
    sc query nginx | find "RUNNING" >nul
    if %errorLevel% equ 0 (
        echo ✓ Nginx service started successfully
    ) else (
        echo ✗ Nginx service failed to start
        echo Trying manual start...
        
        :: Try manual start
        cd /d nginx
        start /b nginx.exe
        timeout /t 3 /nobreak >nul
        
        :: Check if Nginx process is running
        tasklist | find "nginx.exe" >nul
        if %errorLevel% equ 0 (
            echo ✓ Nginx started manually
        ) else (
            echo ✗ Nginx failed to start manually
        )
    )
) else (
    echo Nginx service is already running
)

echo.

echo [3/4] Starting Django service...

if %DJANGO_RUNNING% equ 0 (
    echo Starting Django service...
    sc start DjangoProjectManager
    timeout /t 5 /nobreak >nul
    
    :: Check if Django started
    sc query DjangoProjectManager | find "RUNNING" >nul
    if %errorLevel% equ 0 (
        echo ✓ Django service started successfully
    ) else (
        echo ✗ Django service failed to start
        echo Trying manual start...
        
        :: Try manual start
        cd /d "%~dp0"
        start /b python manage.py runserver 127.0.0.1:8000
        timeout /t 3 /nobreak >nul
        
        :: Check if Python process is running
        tasklist | find "python.exe" >nul
        if %errorLevel% equ 0 (
            echo ✓ Django started manually
        ) else (
            echo ✗ Django failed to start manually
        )
    )
) else (
    echo Django service is already running
)

echo.

echo [4/4] Final status check...

:: Final status check
echo Final service status:
echo.
echo Nginx service:
sc query nginx
echo.
echo Django service:
sc query DjangoProjectManager
echo.

:: Test website accessibility
echo Testing website accessibility...
curl -s --max-time 10 http://projecthelal.rcs.ir >nul 2>&1
if %errorLevel% equ 0 (
    echo ✓ Website is accessible at http://projecthelal.rcs.ir
) else (
    echo ✗ Website is not accessible
)

echo.
echo ========================================
echo Service Start Complete!
echo ========================================
echo.
echo You can now test your website:
echo - HTTP: http://projecthelal.rcs.ir
echo - Admin: http://projecthelal.rcs.ir/admin/
echo.
echo To check deployment status: check_deployment_status.bat
echo.
pause
exit /b 0
