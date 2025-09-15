@echo off
echo ========================================
echo Fix Duplicate Column Issue
echo ========================================

echo.
echo This script will fix the duplicate 'file_mime_type' column issue.
echo.

set /p CONFIRM="Do you want to fix the duplicate column issue? (y/n): "
if /i not "%CONFIRM%"=="y" (
    echo Operation cancelled.
    pause
    exit /b 0
)

echo.
echo [1/5] Checking database schema...

:: Check if the column exists
mysql -u django_user -pdjango_password_2024 -e "USE project_manager_db; DESCRIBE creator_subproject_documentfile;" 2>nul | find "file_mime_type" >nul
if %errorLevel% equ 0 (
    echo ✓ Column 'file_mime_type' already exists in database
    echo This is causing the migration conflict
) else (
    echo ✗ Column 'file_mime_type' does not exist
    echo The migration should work normally
)

echo.
echo [2/5] Checking migration status...

:: Show migration status
python manage.py showmigrations creator_subproject
if %errorLevel% neq 0 (
    echo ERROR: Cannot show migration status
    pause
    exit /b 1
)

echo.
echo [3/5] Marking problematic migration as applied...

:: Mark the problematic migration as applied without running it
echo Marking migration 0003_documentfile_file_mime_type as applied...
python manage.py migrate creator_subproject 0003 --fake
if %errorLevel% neq 0 (
    echo ERROR: Failed to fake apply migration
    pause
    exit /b 1
)

echo ✓ Migration marked as applied

echo.
echo [4/5] Applying remaining migrations...

:: Apply remaining migrations
python manage.py migrate
if %errorLevel% neq 0 (
    echo ERROR: Failed to apply remaining migrations
    pause
    exit /b 1
)

echo ✓ Remaining migrations applied successfully

echo.
echo [5/5] Testing Django setup...

:: Test Django setup
python manage.py check
if %errorLevel% neq 0 (
    echo ERROR: Django check failed
    pause
    exit /b 1
)

echo ✓ Django check passed

echo.
echo ========================================
echo Duplicate Column Fix Complete!
echo ========================================
echo.
echo The duplicate column issue has been resolved.
echo.
echo You can now run:
echo python manage.py collectstatic --noinput
echo.
echo Or continue with the deployment script:
echo dynamic_deploy_clean.bat
echo.
pause
exit /b 0
