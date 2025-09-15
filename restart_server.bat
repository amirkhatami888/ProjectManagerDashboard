@echo off
setlocal enabledelayedexpansion

echo ========================================
echo Restart Django Website Server
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
echo Restarting Django website services...
echo.

:: Stop services
echo Stopping services...
echo.
echo Stopping Django service...
sc stop %SERVICE_NAME% >nul 2>&1
if %errorLevel% equ 0 (
    echo ✓ Django service stopped
) else (
    echo - Django service was not running
)

echo Stopping nginx service...
sc stop %NGINX_SERVICE% >nul 2>&1
if %errorLevel% equ 0 (
    echo ✓ nginx service stopped
) else (
    echo - nginx service was not running
)

:: Wait for services to stop completely
echo.
echo Waiting for services to stop completely...
timeout /t 5 /nobreak >nul

:: Start services
echo.
echo Starting services...
echo.
echo Starting nginx service...
sc start %NGINX_SERVICE%
if %errorLevel% equ 0 (
    echo ✓ nginx service started
) else (
    echo ✗ Failed to start nginx service
)

:: Wait for nginx to start
timeout /t 3 /nobreak >nul

echo Starting Django service...
sc start %SERVICE_NAME%
if %errorLevel% equ 0 (
    echo ✓ Django service started
) else (
    echo ✗ Failed to start Django service
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

echo.
echo ========================================
echo SERVER RESTARTED SUCCESSFULLY!
echo ========================================
echo.
echo Your Django website has been restarted.
echo.
echo Access your website at:
echo - http://localhost
echo - http://your-domain.com (if configured)
echo.
echo Service Management:
echo - Stop server: stop_server.bat
echo - Start server: start_server.bat
echo - Service manager: advanced_service_manager.bat
echo.
echo ========================================

pause
