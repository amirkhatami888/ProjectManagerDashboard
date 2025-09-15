@echo off
echo ========================================
echo Fix Session Manager Models
echo ========================================

echo.
echo This script will fix the session_manager models and create migrations.
echo.

set /p CONFIRM="Do you want to fix session_manager models? (y/n): "
if /i not "%CONFIRM%"=="y" (
    echo Operation cancelled.
    pause
    exit /b 0
)

echo.
echo [1/4] Creating session_manager migrations directory...

:: Create migrations directory if it doesn't exist
if not exist "session_manager\migrations" (
    mkdir "session_manager\migrations"
    echo ✓ Created migrations directory
) else (
    echo ✓ Migrations directory already exists
)

:: Create __init__.py in migrations directory
if not exist "session_manager\migrations\__init__.py" (
    echo. > "session_manager\migrations\__init__.py"
    echo ✓ Created __init__.py in migrations directory
) else (
    echo ✓ __init__.py already exists in migrations directory
)

echo.
echo [2/4] Creating initial migration for session_manager...

:: Create initial migration
python manage.py makemigrations session_manager
if %errorLevel% neq 0 (
    echo ERROR: Failed to create migration for session_manager
    echo This might be due to model issues
    pause
    exit /b 1
)

echo ✓ Migration created successfully

echo.
echo [3/4] Running migrations...

:: Run migrations
python manage.py migrate
if %errorLevel% neq 0 (
    echo ERROR: Failed to run migrations
    echo This might be due to database issues
    pause
    exit /b 1
)

echo ✓ Migrations completed successfully

echo.
echo [4/4] Testing Django setup...

:: Test Django setup
python manage.py check
if %errorLevel% neq 0 (
    echo ERROR: Django check failed
    echo There might still be issues with the models
    pause
    exit /b 1
)

echo ✓ Django check passed

echo.
echo ========================================
echo Session Manager Models Fix Complete!
echo ========================================
echo.
echo The session_manager models have been fixed and migrations created.
echo.
echo You can now run:
echo python manage.py collectstatic --noinput
echo.
echo Or continue with the deployment script:
echo dynamic_deploy_clean.bat
echo.
pause
exit /b 0
