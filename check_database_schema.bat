@echo off
echo ========================================
echo Check Database Schema
echo ========================================

echo.
echo This script will check the database schema and show table structures.
echo.

echo [1/4] Checking database connection...

:: Test database connection
mysql -u django_user -pdjango_password_2024 -e "USE project_manager_db; SELECT 1;" >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Cannot connect to database
    pause
    exit /b 1
)

echo ✓ Database connection successful

echo.
echo [2/4] Listing all tables...

:: List all tables
echo Database tables:
mysql -u django_user -pdjango_password_2024 -e "USE project_manager_db; SHOW TABLES;"
if %errorLevel% neq 0 (
    echo ERROR: Cannot list tables
    pause
    exit /b 1
)

echo.
echo [3/4] Checking creator_subproject_documentfile table structure...

:: Check the problematic table structure
echo Table structure for creator_subproject_documentfile:
mysql -u django_user -pdjango_password_2024 -e "USE project_manager_db; DESCRIBE creator_subproject_documentfile;"
if %errorLevel% neq 0 (
    echo ERROR: Cannot describe table
    pause
    exit /b 1
)

echo.
echo [4/4] Checking migration status...

:: Show migration status
echo Migration status for creator_subproject:
python manage.py showmigrations creator_subproject
if %errorLevel% neq 0 (
    echo ERROR: Cannot show migration status
    pause
    exit /b 1
)

echo.
echo ========================================
echo Database Schema Check Complete!
echo ========================================
echo.
echo If you see 'file_mime_type' in the table structure, it means the column already exists.
echo This is why the migration is failing with "Duplicate column name" error.
echo.
echo To fix this, run: fix_duplicate_column.bat
echo.
pause
exit /b 0
