@echo off
echo ========================================
echo Fix Nginx Directories
echo ========================================

echo.
echo This script will create the missing Nginx directories.
echo.

echo [1/4] Stopping Nginx service...

:: Stop Nginx service
sc stop nginx
timeout /t 3 /nobreak >nul

:: Kill any remaining Nginx processes
taskkill /f /im nginx.exe >nul 2>&1
timeout /t 2 /nobreak >nul

echo ✓ Nginx stopped

echo.
echo [2/4] Creating Nginx directories...

:: Create logs directory
if not exist "nginx\logs" (
    mkdir "nginx\logs"
    echo ✓ Created nginx\logs directory
) else (
    echo ✓ nginx\logs directory already exists
)

:: Create temp directory
if not exist "nginx\temp" (
    mkdir "nginx\temp"
    echo ✓ Created nginx\temp directory
) else (
    echo ✓ nginx\temp directory already exists
)

:: Create client_body_temp subdirectory
if not exist "nginx\temp\client_body_temp" (
    mkdir "nginx\temp\client_body_temp"
    echo ✓ Created nginx\temp\client_body_temp directory
) else (
    echo ✓ nginx\temp\client_body_temp directory already exists
)

:: Create proxy_temp subdirectory
if not exist "nginx\temp\proxy_temp" (
    mkdir "nginx\temp\proxy_temp"
    echo ✓ Created nginx\temp\proxy_temp directory
) else (
    echo ✓ nginx\temp\proxy_temp directory already exists
)

:: Create fastcgi_temp subdirectory
if not exist "nginx\temp\fastcgi_temp" (
    mkdir "nginx\temp\fastcgi_temp"
    echo ✓ Created nginx\temp\fastcgi_temp directory
) else (
    echo ✓ nginx\temp\fastcgi_temp directory already exists
)

:: Create uwsgi_temp subdirectory
if not exist "nginx\temp\uwsgi_temp" (
    mkdir "nginx\temp\uwsgi_temp"
    echo ✓ Created nginx\temp\uwsgi_temp directory
) else (
    echo ✓ nginx\temp\uwsgi_temp directory already exists
)

:: Create scgi_temp subdirectory
if not exist "nginx\temp\scgi_temp" (
    mkdir "nginx\temp\scgi_temp"
    echo ✓ Created nginx\temp\scgi_temp directory
) else (
    echo ✓ nginx\temp\scgi_temp directory already exists
)

echo.
echo [3/4] Testing Nginx configuration...

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
echo [4/4] Starting Nginx service...

:: Start Nginx service
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
        echo Check nginx\logs\error.log for details
    )
    cd /d "%~dp0"
)

echo.
echo ========================================
echo Nginx Directories Fix Complete!
echo ========================================
echo.
echo Nginx status:
sc query nginx
echo.
pause
exit /b 0
