@echo off
echo ========================================
echo Django Setup Test Script
echo ========================================

echo.
echo This script will test Django setup step by step.
echo.

set /p CONFIRM="Do you want to test Django setup? (y/n): "
if /i not "%CONFIRM%"=="y" (
    echo Operation cancelled.
    pause
    exit /b 0
)

echo.
echo [1/4] Testing Django import...

:: Test basic Django import
python -c "import django; print('Django version:', django.get_version())"
if %errorLevel% neq 0 (
    echo ERROR: Django import failed
    pause
    exit /b 1
)

echo ✓ Django import successful

echo.
echo [2/4] Testing Django settings...

:: Test Django settings
python -c "import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project_dashboard.settings'); import django; django.setup(); print('Django settings loaded successfully')"
if %errorLevel% neq 0 (
    echo ERROR: Django settings failed
    echo This might be due to missing modules or configuration issues
    pause
    exit /b 1
)

echo ✓ Django settings loaded successfully

echo.
echo [3/4] Testing Django migrations...

:: Test migrations
echo Running Django migrations...
python manage.py migrate --noinput
if %errorLevel% neq 0 (
    echo ERROR: Django migrations failed
    pause
    exit /b 1
)

echo ✓ Django migrations completed successfully

echo.
echo [4/4] Testing static files collection...

:: Test static files collection
echo Collecting static files...
python manage.py collectstatic --noinput
if %errorLevel% neq 0 (
    echo ERROR: Static files collection failed
    pause
    exit /b 1
)

echo ✓ Static files collected successfully

echo.
echo ========================================
echo Django Setup Test Complete!
echo ========================================
echo.
echo Django is now ready for deployment.
echo.
echo You can now run the deployment script:
echo dynamic_deploy_clean.bat
echo.
pause
exit /b 0
