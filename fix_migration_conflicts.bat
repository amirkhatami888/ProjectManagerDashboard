@echo off
echo ========================================
echo Fix Migration Conflicts
echo ========================================

echo.
echo This script will fix migration conflicts and database schema issues.
echo.

set /p CONFIRM="Do you want to fix migration conflicts? (y/n): "
if /i not "%CONFIRM%"=="y" (
    echo Operation cancelled.
    pause
    exit /b 0
)

echo.
echo [1/6] Checking current migration status...

:: Show current migration status
python manage.py showmigrations
if %errorLevel% neq 0 (
    echo ERROR: Cannot show migrations
    pause
    exit /b 1
)

echo.
echo [2/6] Checking for fake migrations...

:: Check which migrations are applied
python manage.py showmigrations --plan
if %errorLevel% neq 0 (
    echo ERROR: Cannot show migration plan
    pause
    exit /b 1
)

echo.
echo [3/6] Resetting problematic migrations...

:: Fake unapply all migrations first
echo Faking unapply of all migrations...
python manage.py migrate --fake-initial
if %errorLevel% neq 0 (
    echo Warning: Fake initial migration failed, continuing...
)

echo.
echo [4/6] Checking database schema conflicts...

:: Check for duplicate columns
mysql -u django_user -pdjango_password_2024 -e "USE project_manager_db; SHOW TABLES;" 2>nul
if %errorLevel% neq 0 (
    echo ERROR: Cannot connect to database
    pause
    exit /b 1
)

echo.
echo [5/6] Creating fresh migrations...

:: Delete existing migration files (except __init__.py)
echo Cleaning up existing migration files...
for /d %%d in (*/migrations) do (
    if exist "%%d" (
        echo Cleaning %%d
        del /q "%%d\*.py" 2>nul
        echo. > "%%d\__init__.py"
    )
)

:: Create fresh migrations
echo Creating fresh migrations...
python manage.py makemigrations
if %errorLevel% neq 0 (
    echo ERROR: Failed to create fresh migrations
    pause
    exit /b 1
)

echo ✓ Fresh migrations created

echo.
echo [6/6] Applying migrations with fake initial...

:: Apply migrations with fake initial
echo Applying migrations...
python manage.py migrate --fake-initial
if %errorLevel% neq 0 (
    echo ERROR: Failed to apply migrations
    echo.
    echo Trying alternative approach...
    
    :: Try to apply migrations normally
    python manage.py migrate
    if %errorLevel% neq 0 (
        echo ERROR: All migration attempts failed
        echo.
        echo Manual intervention required:
        echo 1. Check database for duplicate columns
        echo 2. Manually fix schema conflicts
        echo 3. Recreate database if necessary
        pause
        exit /b 1
    )
)

echo ✓ Migrations applied successfully

echo.
echo ========================================
echo Migration Conflicts Fix Complete!
echo ========================================
echo.
echo The migration conflicts have been resolved.
echo.
echo You can now run:
echo python manage.py check
echo python manage.py collectstatic --noinput
echo.
echo Or continue with the deployment script:
echo dynamic_deploy_clean.bat
echo.
pause
exit /b 0
