@echo off
echo ========================================
echo Test Django User Database Connection
echo ========================================

echo.
echo This script will test the database connection using the django_user.
echo.

echo [1/4] Testing MySQL root connection...

:: Test MySQL root connection first
mysql -u root -pAmir137667318@ -e "SELECT 1;" >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Cannot connect to MySQL with root password
    echo Please check MySQL is running and password is correct
    pause
    exit /b 1
)

echo ✓ MySQL root connection successful

echo.
echo [2/4] Testing django_user connection...

:: Test django_user connection
mysql -u django_user -pdjango_password_2024 -e "SELECT 1;" >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Cannot connect with django_user
    echo This might be due to:
    echo 1. User doesn't exist
    echo 2. Wrong password
    echo 3. User doesn't have proper privileges
    echo.
    echo Let's check and fix this...
    
    :: Check if user exists
    mysql -u root -pAmir137667318@ -e "SELECT User, Host FROM mysql.user WHERE User='django_user';" | find "django_user" >nul 2>&1
    if %errorLevel% neq 0 (
        echo ✗ User 'django_user' does not exist, creating...
        mysql -u root -pAmir137667318@ -e "CREATE USER 'django_user'@'localhost' IDENTIFIED BY 'django_password_2024';"
        if %errorLevel% neq 0 (
            echo ERROR: Failed to create user
            pause
            exit /b 1
        )
        echo ✓ User created successfully
    ) else (
        echo ✓ User 'django_user' exists
    )
    
    :: Grant privileges
    echo Granting privileges to django_user...
    mysql -u root -pAmir137667318@ -e "GRANT ALL PRIVILEGES ON project_manager_db.* TO 'django_user'@'localhost'; FLUSH PRIVILEGES;"
    if %errorLevel% neq 0 (
        echo ERROR: Failed to grant privileges
        pause
        exit /b 1
    )
    echo ✓ Privileges granted successfully
    
    :: Test connection again
    mysql -u django_user -pdjango_password_2024 -e "SELECT 1;" >nul 2>&1
    if %errorLevel% neq 0 (
        echo ERROR: Still cannot connect with django_user after setup
        pause
        exit /b 1
    )
) else (
    echo ✓ django_user connection successful
)

echo.
echo [3/4] Testing database access...

:: Test database access
mysql -u django_user -pdjango_password_2024 -e "USE project_manager_db; SELECT 1;" >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: django_user cannot access project_manager_db database
    echo Granting database privileges...
    mysql -u root -pAmir137667318@ -e "GRANT ALL PRIVILEGES ON project_manager_db.* TO 'django_user'@'localhost'; FLUSH PRIVILEGES;"
    if %errorLevel% neq 0 (
        echo ERROR: Failed to grant database privileges
        pause
        exit /b 1
    )
    echo ✓ Database privileges granted
    
    :: Test again
    mysql -u django_user -pdjango_password_2024 -e "USE project_manager_db; SELECT 1;" >nul 2>&1
    if %errorLevel% neq 0 (
        echo ERROR: Still cannot access database
        pause
        exit /b 1
    )
) else (
    echo ✓ Database access successful
)

echo.
echo [4/4] Testing Django connection...

:: Test Django connection
python manage.py check --database default
if %errorLevel% neq 0 (
    echo ERROR: Django database connection test failed
    echo.
    echo This might be due to:
    echo 1. Missing .env file
    echo 2. Django not reading .env file properly
    echo 3. Settings configuration issue
    echo.
    echo Try running: create_env_file.bat
    pause
    exit /b 1
)

echo ✓ Django database connection test successful

echo.
echo ========================================
echo Database Connection Test Complete!
echo ========================================
echo.
echo All database connections are working properly:
echo - MySQL root: ✓
echo - django_user: ✓
echo - Database access: ✓
echo - Django connection: ✓
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
