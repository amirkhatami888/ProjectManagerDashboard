@echo off
echo ========================================
echo Database Connection Test
echo ========================================

echo.
echo This script will test the database connection step by step.
echo.

set /p MYSQL_ROOT_PASSWORD="Enter MySQL root password: "
if "%MYSQL_ROOT_PASSWORD%"=="" (
    echo ERROR: MySQL root password is required
    pause
    exit /b 1
)

echo.
echo [1/4] Testing MySQL root connection...

:: Test MySQL root connection
mysql -u root -p%MYSQL_ROOT_PASSWORD% -e "SELECT 1;" >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Cannot connect to MySQL with root password
    echo Please check:
    echo 1. MySQL server is running
    echo 2. Root password is correct
    echo 3. MySQL is accessible from command line
    pause
    exit /b 1
)

echo ✓ MySQL root connection successful

echo.
echo [2/4] Checking if database exists...

:: Check if database exists
mysql -u root -p%MYSQL_ROOT_PASSWORD% -e "USE project_manager_db; SELECT 1;" >nul 2>&1
if %errorLevel% neq 0 (
    echo ✗ Database 'project_manager_db' does not exist
    echo Creating database...
    mysql -u root -p%MYSQL_ROOT_PASSWORD% -e "CREATE DATABASE IF NOT EXISTS project_manager_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
    if %errorLevel% neq 0 (
        echo ERROR: Failed to create database
        pause
        exit /b 1
    )
    echo ✓ Database created successfully
) else (
    echo ✓ Database 'project_manager_db' exists
)

echo.
echo [3/4] Checking if user exists...

:: Check if user exists
mysql -u root -p%MYSQL_ROOT_PASSWORD% -e "SELECT User, Host FROM mysql.user WHERE User='django_user';" | find "django_user" >nul 2>&1
if %errorLevel% neq 0 (
    echo ✗ User 'django_user' does not exist
    echo Creating user...
    mysql -u root -p%MYSQL_ROOT_PASSWORD% -e "CREATE USER IF NOT EXISTS 'django_user'@'localhost' IDENTIFIED BY 'django_password_2024';"
    if %errorLevel% neq 0 (
        echo ERROR: Failed to create user
        pause
        exit /b 1
    )
    echo ✓ User created successfully
) else (
    echo ✓ User 'django_user' exists
)

echo.
echo [4/4] Granting privileges and testing Django connection...

:: Grant privileges
mysql -u root -p%MYSQL_ROOT_PASSWORD% -e "GRANT ALL PRIVILEGES ON project_manager_db.* TO 'django_user'@'localhost'; FLUSH PRIVILEGES;"
if %errorLevel% neq 0 (
    echo ERROR: Failed to grant privileges
    pause
    exit /b 1
)

echo ✓ Privileges granted successfully

:: Test Django connection
echo Testing Django database connection...
python manage.py check --database default
if %errorLevel% neq 0 (
    echo ERROR: Django database connection test failed
    echo.
    echo This might be due to:
    echo 1. Missing .env file
    echo 2. Incorrect database configuration
    echo 3. Django settings issues
    echo.
    echo Try running: fix_django_database.bat
    pause
    exit /b 1
)

echo ✓ Django database connection test successful

echo.
echo ========================================
echo Database Connection Test Complete!
echo ========================================
echo.
echo All database connections are working properly.
echo.
echo You can now run:
echo python manage.py migrate
echo python manage.py collectstatic --noinput
echo.
echo Or continue with the deployment script:
echo dynamic_deploy_clean.bat
echo.
pause
exit /b 0
