@echo off
echo ========================================
echo Fix Nginx Service
echo ========================================

echo.
echo This script will diagnose and fix Nginx service issues.
echo.

echo [1/6] Checking Nginx service status...

:: Check Nginx service status
sc query nginx
if %errorLevel% neq 0 (
    echo ERROR: Cannot query Nginx service
    pause
    exit /b 1
)

echo.
echo [2/6] Checking Nginx configuration...

:: Check if nginx.conf exists
if not exist "nginx\conf\nginx.conf" (
    echo ERROR: nginx.conf not found at nginx\conf\nginx.conf
    pause
    exit /b 1
)

echo ✓ nginx.conf found

:: Test Nginx configuration
echo Testing Nginx configuration...
nginx\nginx.exe -t
if %errorLevel% neq 0 (
    echo ERROR: Nginx configuration test failed
    echo.
    echo Checking nginx.conf for issues...
    echo.
    echo First 20 lines of nginx.conf:
    type nginx\conf\nginx.conf | more
    echo.
    echo Please check the configuration file for syntax errors
    pause
    exit /b 1
)

echo ✓ Nginx configuration is valid

echo.
echo [3/6] Checking for port conflicts...

:: Check if port 80 is in use
netstat -an | find ":80 " >nul 2>&1
if %errorLevel% equ 0 (
    echo WARNING: Port 80 is already in use
    echo.
    echo Processes using port 80:
    netstat -ano | find ":80 "
    echo.
    echo You may need to stop the conflicting service
) else (
    echo ✓ Port 80 is available
)

echo.
echo [4/6] Checking Nginx logs...

:: Check Nginx error log
if exist "nginx\logs\error.log" (
    echo Nginx error log (last 10 lines):
    powershell -Command "Get-Content 'nginx\logs\error.log' | Select-Object -Last 10"
    echo.
) else (
    echo No error log found
)

echo.
echo [5/6] Stopping and restarting Nginx service...

:: Stop Nginx service
echo Stopping Nginx service...
sc stop nginx
timeout /t 3 /nobreak >nul

:: Start Nginx service
echo Starting Nginx service...
sc start nginx
timeout /t 5 /nobreak >nul

:: Check if Nginx started
sc query nginx | find "RUNNING" >nul
if %errorLevel% equ 0 (
    echo ✓ Nginx service started successfully
) else (
    echo ERROR: Nginx service still not running
    echo.
    echo [6/6] Trying manual Nginx start...
    
    :: Try to start Nginx manually
    echo Starting Nginx manually...
    cd /d nginx
    start /b nginx.exe
    timeout /t 3 /nobreak >nul
    
    :: Check if Nginx process is running
    tasklist | find "nginx.exe" >nul
    if %errorLevel% equ 0 (
        echo ✓ Nginx started manually
        echo.
        echo Note: Nginx is running manually, not as a service
        echo You may need to configure it as a service later
    ) else (
        echo ERROR: Nginx failed to start manually
        echo.
        echo Troubleshooting steps:
        echo 1. Check nginx.conf for syntax errors
        echo 2. Check if port 80 is available
        echo 3. Check Windows Firewall settings
        echo 4. Check Nginx logs for errors
        pause
        exit /b 1
    )
)

echo.
echo ========================================
echo Nginx Service Fix Complete!
echo ========================================
echo.
echo Nginx status:
sc query nginx
echo.
echo You can now test the website:
echo - HTTP: http://projecthelal.rcs.ir
echo - Admin: http://projecthelal.rcs.ir/admin/
echo.
echo Or continue with the deployment script:
echo dynamic_deploy_clean.bat
echo.
pause
exit /b 0
