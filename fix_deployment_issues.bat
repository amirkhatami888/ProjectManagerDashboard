@echo off
echo ========================================
echo Fix Deployment Issues
echo ========================================

echo.
echo This script will fix all deployment issues.
echo.

echo [1/6] Creating required directories...

:: Create logs directory
if not exist "logs" (
    mkdir "logs"
    echo ✓ Created logs directory
) else (
    echo ✓ logs directory already exists
)

:: Create Nginx directories
if not exist "nginx\logs" (
    mkdir "nginx\logs"
    echo ✓ Created nginx\logs directory
) else (
    echo ✓ nginx\logs directory already exists
)

if not exist "nginx\temp" (
    mkdir "nginx\temp"
    echo ✓ Created nginx\temp directory
) else (
    echo ✓ nginx\temp directory already exists
)

if not exist "nginx\temp\client_body_temp" (
    mkdir "nginx\temp\client_body_temp"
    echo ✓ Created nginx\temp\client_body_temp directory
) else (
    echo ✓ nginx\temp\client_body_temp directory already exists
)

echo.
echo [2/6] Stopping all services...

:: Stop all services
sc stop nginx >nul 2>&1
sc stop DjangoProjectManager >nul 2>&1
timeout /t 3 /nobreak >nul

:: Kill any remaining processes
taskkill /f /im nginx.exe >nul 2>&1
taskkill /f /im python.exe >nul 2>&1
timeout /t 2 /nobreak >nul

echo ✓ All services stopped

echo.
echo [3/6] Testing Django configuration...

:: Test Django configuration
python manage.py check
if %errorLevel% neq 0 (
    echo ERROR: Django configuration check failed
    echo Please fix Django configuration issues first
    pause
    exit /b 1
)

echo ✓ Django configuration is valid

echo.
echo [4/6] Testing Nginx configuration...

:: Test Nginx configuration
cd /d nginx
nginx.exe -t
if %errorLevel% neq 0 (
    echo ERROR: Nginx configuration test failed
    cd /d "%~dp0"
    pause
    exit /b 1
)

echo ✓ Nginx configuration is valid
cd /d "%~dp0"

echo.
echo [5/6] Starting services...

:: Start Nginx service
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
    cd /d "%~dp0"
)

:: Start Django service
echo Starting Django service...
sc start DjangoProjectManager
timeout /t 10 /nobreak >nul

:: Check if Django started
sc query DjangoProjectManager | find "RUNNING" >nul
if %errorLevel% equ 0 (
    echo ✓ Django service started successfully
) else (
    echo ✗ Django service failed to start
    echo Trying manual start...
    
    :: Try manual start
    start /b python manage.py runserver 127.0.0.1:8000
    timeout /t 5 /nobreak >nul
    
    :: Check if Python process is running
    tasklist | find "python.exe" >nul
    if %errorLevel% equ 0 (
        echo ✓ Django started manually
    ) else (
        echo ✗ Django failed to start manually
    )
)

echo.
echo [6/6] Testing website accessibility...

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
echo Deployment Issues Fix Complete!
echo ========================================
echo.
echo Final service status:
echo.
echo Nginx service:
sc query nginx
echo.
echo Django service:
sc query DjangoProjectManager
echo.
echo Website URLs:
echo - HTTP: http://projecthelal.rcs.ir
echo - Admin: http://projecthelal.rcs.ir/admin/
echo.
pause
exit /b 0