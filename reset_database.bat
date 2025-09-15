@echo off
echo ========================================
echo Reset Database
echo ========================================

echo.
echo WARNING: This will completely reset the database!
echo All data will be lost!
echo.

set /p CONFIRM="Are you sure you want to reset the database? (y/n): "
if /i not "%CONFIRM%"=="y" (
    echo Operation cancelled.
    pause
    exit /b 0
)

echo.
echo [1/5] Dropping and recreating database...

:: Drop and recreate database
mysql -u root -pAmir137667318@ -e "DROP DATABASE IF EXISTS project_manager_db; CREATE DATABASE project_manager_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
if %errorLevel% neq 0 (
    echo ERROR: Failed to recreate database
    pause
    exit /b 1
)

echo ✓ Database recreated successfully

echo.
echo [2/5] Recreating user and privileges...

:: Recreate user and privileges
mysql -u root -pAmir137667318@ -e "DROP USER IF EXISTS 'django_user'@'localhost'; CREATE USER 'django_user'@'localhost' IDENTIFIED BY 'django_password_2024'; GRANT ALL PRIVILEGES ON project_manager_db.* TO 'django_user'@'localhost'; FLUSH PRIVILEGES;"
if %errorLevel% neq 0 (
    echo ERROR: Failed to recreate user
    pause
    exit /b 1
)

echo ✓ User recreated successfully

echo.
echo [3/5] Cleaning migration files...

:: Clean migration files
for /d %%d in (*/migrations) do (
    if exist "%%d" (
        echo Cleaning %%d
        del /q "%%d\*.py" 2>nul
        echo. > "%%d\__init__.py"
    )
)

echo ✓ Migration files cleaned

echo.
echo [4/5] Creating fresh migrations...

:: Create fresh migrations
python manage.py makemigrations
if %errorLevel% neq 0 (
    echo ERROR: Failed to create fresh migrations
    pause
    exit /b 1
)

echo ✓ Fresh migrations created

echo.
echo [5/5] Applying migrations...

:: Apply migrations
python manage.py migrate
if %errorLevel% neq 0 (
    echo ERROR: Failed to apply migrations
    pause
    exit /b 1
)

echo ✓ Migrations applied successfully

echo.
echo ========================================
echo Database Reset Complete!
echo ========================================
echo.
echo The database has been completely reset and recreated.
echo.
echo Database Information:
echo - Database: project_manager_db
echo - User: django_user
echo - Password: django_password_2024
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
