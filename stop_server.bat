@echo off
setlocal enabledelayedexpansion

echo ========================================
echo Stop Django Website Server
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
echo Stopping Django website services...
echo.

:: Stop Django service
echo Stopping Django service (%SERVICE_NAME%)...
sc stop %SERVICE_NAME% >nul 2>&1
if %errorLevel% equ 0 (
    echo ✓ Django service stopped successfully
) else (
    echo ✗ Failed to stop Django service (may not be running)
)

:: Wait a moment for Django to stop gracefully
timeout /t 3 /nobreak >nul

:: Stop nginx service
echo Stopping nginx service...
sc stop %NGINX_SERVICE% >nul 2>&1
if %errorLevel% equ 0 (
    echo ✓ nginx service stopped successfully
) else (
    echo ✗ Failed to stop nginx service (may not be running)
)

:: Wait for nginx to stop
timeout /t 2 /nobreak >nul

:: Check service status
echo.
echo Checking service status...
echo.
echo Django Service Status:
sc query %SERVICE_NAME% | find "STOPPED" >nul
if %errorLevel% equ 0 (
    echo ✓ Django service is stopped
) else (
    sc query %SERVICE_NAME% | find "RUNNING" >nul
    if %errorLevel% equ 0 (
        echo ✗ Django service is still running
    ) else (
        echo - Django service is not installed
    )
)

echo.
echo Nginx Service Status:
sc query %NGINX_SERVICE% | find "STOPPED" >nul
if %errorLevel% equ 0 (
    echo ✓ nginx service is stopped
) else (
    sc query %NGINX_SERVICE% | find "RUNNING" >nul
    if %errorLevel% equ 0 (
        echo ✗ nginx service is still running
    ) else (
        echo - nginx service is not installed
    )
)

:: Check if any processes are still running
echo.
echo Checking for running processes...
tasklist | findstr "nginx.exe" >nul
if %errorLevel% equ 0 (
    echo ⚠ nginx process is still running
    echo Killing nginx processes...
    taskkill /f /im nginx.exe >nul 2>&1
    if %errorLevel% equ 0 (
        echo ✓ nginx processes killed
    ) else (
        echo ✗ Failed to kill nginx processes
    )
) else (
    echo ✓ No nginx processes running
)

tasklist | findstr "python.exe" >nul
if %errorLevel% equ 0 (
    echo ⚠ Python processes are still running
    echo Note: Other Python applications may be running
    echo To kill Django specifically, use: taskkill /f /im python.exe
) else (
    echo ✓ No Python processes running
)

:: Check port status
echo.
echo Checking port status...
netstat -an | findstr ":80 " >nul
if %errorLevel% equ 0 (
    echo ⚠ Port 80 is still in use
) else (
    echo ✓ Port 80 is free
)

netstat -an | findstr ":443 " >nul
if %errorLevel% equ 0 (
    echo ⚠ Port 443 is still in use
) else (
    echo ✓ Port 443 is free
)

netstat -an | findstr ":8000 " >nul
if %errorLevel% equ 0 (
    echo ⚠ Port 8000 is still in use
) else (
    echo ✓ Port 8000 is free
)

echo.
echo ========================================
echo SERVER STOPPED SUCCESSFULLY!
echo ========================================
echo.
echo All Django website services have been stopped.
echo.
echo To start the server again, run:
echo - start_server.bat
echo - Or use: sc start nginx && sc start DjangoProjectManager
echo.
echo To restart the server, run:
echo - restart_server.bat
echo.
echo ========================================

pause
