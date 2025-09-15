@echo off
setlocal enabledelayedexpansion

echo ========================================
echo Start Django Website Server
echo ========================================

:: Set service names
set SERVICE_NAME=DjangoProjectManager
set NGINX_SERVICE=nginx

:: Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This script must be run as Administrator
    echo Right-click and select "Run as administrator"
    pause
    exit /b 1
)

echo.
echo Starting Django website services...
echo.

:: Start nginx service first
echo Starting nginx service...
sc start %NGINX_SERVICE%
if %errorLevel% equ 0 (
    echo ✓ nginx service started successfully
) else (
    echo ✗ Failed to start nginx service
    echo Checking if service exists...
    sc query %NGINX_SERVICE% >nul 2>&1
    if %errorLevel% neq 0 (
        echo Service not found. Please run deployment script first.
        pause
        exit /b 1
    )
)

:: Wait for nginx to start
timeout /t 3 /nobreak >nul

:: Start Django service
echo Starting Django service (%SERVICE_NAME%)...
sc start %SERVICE_NAME%
if %errorLevel% equ 0 (
    echo ✓ Django service started successfully
) else (
    echo ✗ Failed to start Django service
    echo Checking if service exists...
    sc query %SERVICE_NAME% >nul 2>&1
    if %errorLevel% neq 0 (
        echo Service not found. Please run deployment script first.
        pause
        exit /b 1
    )
)

:: Wait for Django to start
timeout /t 5 /nobreak >nul

:: Check service status
echo.
echo Checking service status...
echo.
echo Nginx Service Status:
sc query %NGINX_SERVICE% | find "RUNNING" >nul
if %errorLevel% equ 0 (
    echo ✓ nginx service is running
) else (
    echo ✗ nginx service is not running
)

echo.
echo Django Service Status:
sc query %SERVICE_NAME% | find "RUNNING" >nul
if %errorLevel% equ 0 (
    echo ✓ Django service is running
) else (
    echo ✗ Django service is not running
)

:: Test connectivity
echo.
echo Testing connectivity...
echo.
echo Testing localhost:80...
curl -I http://localhost 2>nul | find "HTTP" >nul
if %errorLevel% equ 0 (
    echo ✓ HTTP (Port 80) is responding
) else (
    echo ✗ HTTP (Port 80) is not responding
)

echo.
echo Testing localhost:8000...
curl -I http://localhost:8000 2>nul | find "HTTP" >nul
if %errorLevel% equ 0 (
    echo ✓ Django (Port 8000) is responding
) else (
    echo ✗ Django (Port 8000) is not responding
)

:: Check port status
echo.
echo Checking port status...
netstat -an | findstr ":80 " >nul
if %errorLevel% equ 0 (
    echo ✓ Port 80 is in use (nginx)
) else (
    echo ✗ Port 80 is not in use
)

netstat -an | findstr ":8000 " >nul
if %errorLevel% equ 0 (
    echo ✓ Port 8000 is in use (Django)
) else (
    echo ✗ Port 8000 is not in use
)

echo.
echo ========================================
echo SERVER STARTED SUCCESSFULLY!
echo ========================================
echo.
echo Your Django website is now running.
echo.
echo Access your website at:
echo - http://localhost
echo - http://your-domain.com (if configured)
echo.
echo Service Management:
echo - Stop server: stop_server.bat
echo - Restart server: restart_server.bat
echo - Service manager: advanced_service_manager.bat
echo.
echo ========================================

pause
