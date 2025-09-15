@echo off
echo ========================================
echo Check Deployment Status
echo ========================================

echo.
echo This script will check the current deployment status.
echo.

echo [1/6] Checking service status...

:: Check Nginx service status
echo Nginx service status:
sc query nginx
echo.

:: Check Django service status
echo Django service status:
sc query DjangoProjectManager
echo.

echo [2/6] Checking if services are actually running...

:: Check if Nginx process is running
tasklist | find "nginx.exe" >nul
if %errorLevel% equ 0 (
    echo ✓ Nginx process is running
    tasklist | find "nginx.exe"
) else (
    echo ✗ Nginx process not found
)

echo.

:: Check if Python/Django process is running
tasklist | find "python.exe" >nul
if %errorLevel% equ 0 (
    echo ✓ Python/Django process is running
    tasklist | find "python.exe"
) else (
    echo ✗ Python/Django process not found
)

echo.

echo [3/6] Testing port connectivity...

:: Test if port 80 is responding
echo Testing port 80...
curl -s --max-time 5 http://localhost:80 >nul 2>&1
if %errorLevel% equ 0 (
    echo ✓ Port 80 is responding
) else (
    echo ✗ Port 80 is not responding
)

:: Test if port 8000 is responding
echo Testing port 8000...
curl -s --max-time 5 http://localhost:8000 >nul 2>&1
if %errorLevel% equ 0 (
    echo ✓ Port 8000 is responding
) else (
    echo ✗ Port 8000 is not responding
)

echo.

echo [4/6] Testing website accessibility...

:: Test if website is accessible
echo Testing website accessibility...
curl -s --max-time 10 http://projecthelal.rcs.ir >nul 2>&1
if %errorLevel% equ 0 (
    echo ✓ Website is accessible at http://projecthelal.rcs.ir
) else (
    echo ✗ Website is not accessible at http://projecthelal.rcs.ir
)

echo.

echo [5/6] Checking Nginx logs...

:: Check Nginx error log
if exist "nginx\logs\error.log" (
    echo Nginx error log (last 5 lines):
    powershell -Command "Get-Content 'nginx\logs\error.log' | Select-Object -Last 5"
    echo.
) else (
    echo No Nginx error log found
)

:: Check Nginx access log
if exist "nginx\logs\access.log" (
    echo Nginx access log (last 5 lines):
    powershell -Command "Get-Content 'nginx\logs\access.log' | Select-Object -Last 5"
    echo.
) else (
    echo No Nginx access log found
)

echo.

echo [6/6] Final deployment summary...

echo ========================================
echo DEPLOYMENT STATUS SUMMARY
echo ========================================
echo.

:: Check if both services are running
sc query nginx | find "RUNNING" >nul
set NGINX_STATUS=%errorLevel%

sc query DjangoProjectManager | find "RUNNING" >nul
set DJANGO_STATUS=%errorLevel%

if %NGINX_STATUS% equ 0 (
    echo ✓ Nginx Service: RUNNING
) else (
    echo ✗ Nginx Service: NOT RUNNING
)

if %DJANGO_STATUS% equ 0 (
    echo ✓ Django Service: RUNNING
) else (
    echo ✗ Django Service: NOT RUNNING
)

echo.
echo Website URLs:
echo - HTTP: http://projecthelal.rcs.ir
echo - Admin: http://projecthelal.rcs.ir/admin/
echo.

if %NGINX_STATUS% equ 0 if %DJANGO_STATUS% equ 0 (
    echo ========================================
    echo 🎉 DEPLOYMENT SUCCESSFUL! 🎉
    echo ========================================
    echo.
    echo Your Django website is now running!
    echo.
    echo You can access it at: http://projecthelal.rcs.ir
    echo Admin panel: http://projecthelal.rcs.ir/admin/
    echo.
    echo Next steps:
    echo 1. Test the website in your browser
    echo 2. Set up SSL certificate (optional)
    echo 3. Configure domain DNS if needed
    echo.
) else (
    echo ========================================
    echo ⚠️  DEPLOYMENT NEEDS ATTENTION
    echo ========================================
    echo.
    echo Some services are not running properly.
    echo.
    echo To fix issues:
    echo 1. Run: fix_nginx_service.bat
    echo 2. Check service logs
    echo 3. Restart services if needed
    echo.
)

echo.
pause
exit /b 0
