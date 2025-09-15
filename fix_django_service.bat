@echo off
echo ========================================
echo Fix Django Service
echo ========================================

echo.
echo This script will fix the Django service startup issue.
echo.

echo [1/5] Stopping Django service...

:: Stop Django service
sc stop DjangoProjectManager
timeout /t 3 /nobreak >nul

:: Kill any remaining Python processes
taskkill /f /im python.exe >nul 2>&1
timeout /t 2 /nobreak >nul

echo ✓ Django service stopped

echo.
echo [2/5] Checking Django configuration...

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
echo [3/5] Testing Django startup manually...

:: Test Django startup manually
echo Testing Django startup...
python manage.py runserver 127.0.0.1:8000 --noreload > django_test.log 2>&1 &
set DJANGO_PID=%!

:: Wait a moment for Django to start
timeout /t 5 /nobreak >nul

:: Check if Django is responding
curl -s --max-time 5 http://127.0.0.1:8000 >nul 2>&1
if %errorLevel% equ 0 (
    echo ✓ Django is responding on port 8000
    :: Kill the test process
    taskkill /f /pid %DJANGO_PID% >nul 2>&1
) else (
    echo ✗ Django is not responding on port 8000
    echo Check django_test.log for details
    type django_test.log
    :: Kill the test process
    taskkill /f /pid %DJANGO_PID% >nul 2>&1
    pause
    exit /b 1
)

echo.
echo [4/5] Reinstalling Django service with NSSM...

:: Delete existing service
sc delete DjangoProjectManager >nul 2>&1

:: Reinstall service with NSSM
echo Reinstalling Django service...
nssm\win64\nssm.exe install DjangoProjectManager "C:\Users\Administrator\AppData\Local\Programs\Python\Python310\python.exe" "runserver 127.0.0.1:8000"
if %errorLevel% neq 0 (
    echo ERROR: Failed to install Django service with NSSM
    pause
    exit /b 1
)

:: Configure Django service
echo Configuring Django service...
nssm\win64\nssm.exe set DjangoProjectManager AppDirectory "C:\Users\Administrator\ProjectManagerDashboard"
nssm\win64\nssm.exe set DjangoProjectManager AppStdout "C:\Users\Administrator\ProjectManagerDashboard\logs\django_stdout.log"
nssm\win64\nssm.exe set DjangoProjectManager AppStderr "C:\Users\Administrator\ProjectManagerDashboard\logs\django_stderr.log"
nssm\win64\nssm.exe set DjangoProjectManager Start SERVICE_AUTO_START
nssm\win64\nssm.exe set DjangoProjectManager DisplayName "Django Project Manager"
nssm\win64\nssm.exe set DjangoProjectManager Description "Django Project Manager Dashboard Application"
nssm\win64\nssm.exe set DjangoProjectManager AppExit Default Restart
nssm\win64\nssm.exe set DjangoProjectManager AppRestartDelay 10000
nssm\win64\nssm.exe set DjangoProjectManager AppThrottle 1500
nssm\win64\nssm.exe set DjangoProjectManager AppStopMethodSkip 0
nssm\win64\nssm.exe set DjangoProjectManager AppStopMethodConsole 30000
nssm\win64\nssm.exe set DjangoProjectManager AppStopMethodWindow 30000
nssm\win64\nssm.exe set DjangoProjectManager AppStopMethodThreads 30000
nssm\win64\nssm.exe set DjangoProjectManager AppEnvironmentExtra "DJANGO_SETTINGS_MODULE=project_dashboard.settings" "PYTHONPATH=C:\Users\Administrator\ProjectManagerDashboard"

echo ✓ Django service configured

echo.
echo [5/5] Starting Django service...

:: Start Django service
sc start DjangoProjectManager
timeout /t 10 /nobreak >nul

:: Check if Django started
sc query DjangoProjectManager | find "RUNNING" >nul
if %errorLevel% equ 0 (
    echo ✓ Django service started successfully
) else (
    echo ✗ Django service failed to start
    echo.
    echo Service status:
    sc query DjangoProjectManager
    echo.
    echo Check logs for details:
    if exist "logs\django_stderr.log" (
        echo Django error log:
        type logs\django_stderr.log
    )
    pause
    exit /b 1
)

echo.
echo ========================================
echo Django Service Fix Complete!
echo ========================================
echo.
echo Django service status:
sc query DjangoProjectManager
echo.
echo You can now test the website:
echo - HTTP: http://projecthelal.rcs.ir
echo - Admin: http://projecthelal.rcs.ir/admin/
echo.
pause
exit /b 0
