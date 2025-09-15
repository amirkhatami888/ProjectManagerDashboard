@echo off
echo ========================================
echo Django Module Fix Script
echo ========================================

echo.
echo This script will fix missing Django modules and continue deployment.
echo.

set /p CONFIRM="Do you want to fix Django modules? (y/n): "
if /i not "%CONFIRM%"=="y" (
    echo Operation cancelled.
    pause
    exit /b 0
)

echo.
echo [1/3] Checking Django project structure...

:: Set project directory
set PROJECT_DIR=%~dp0

echo Project Directory: %PROJECT_DIR%

:: Check if manage.py exists
if not exist "%PROJECT_DIR%manage.py" (
    echo ERROR: manage.py not found
    echo Please run this script from the Django project root directory
    pause
    exit /b 1
)

echo ✓ manage.py found

echo.
echo [2/3] Running Django migrations...

:: Run migrations
echo Running Django migrations...
python manage.py migrate --noinput

if %errorLevel% equ 0 (
    echo ✓ Migrations completed successfully
) else (
    echo ✗ Migrations failed
    echo Please check the error messages above
    pause
    exit /b 1
)

echo.
echo [3/3] Collecting static files...

:: Collect static files
echo Collecting static files...
python manage.py collectstatic --noinput

if %errorLevel% equ 0 (
    echo ✓ Static files collected successfully
) else (
    echo ✗ Static file collection failed
    echo Please check the error messages above
    pause
    exit /b 1
)

echo.
echo ========================================
echo Django Module Fix Complete!
echo ========================================
echo.
echo Django is now ready for deployment.
echo.
echo You can now run the deployment script:
echo dynamic_deploy_clean.bat
echo.
echo Or continue with the current deployment process.
echo.
pause
exit /b 0
