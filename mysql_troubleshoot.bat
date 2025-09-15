@echo off
echo ========================================
echo MySQL Troubleshooting Tool
echo ========================================

echo.
echo Testing MySQL connection with different methods...
echo.

:: Test 1: Basic connection test
echo [1/5] Testing basic MySQL connection...
mysql --version >nul 2>&1
if %errorLevel% equ 0 (
    echo ✓ MySQL client is available
) else (
    echo ✗ MySQL client not found in PATH
    echo Please ensure MySQL is installed and added to PATH
    pause
    exit /b 1
)

:: Test 2: Test connection without password
echo.
echo [2/5] Testing connection without password...
mysql -u root -e "SELECT 1;" >nul 2>&1
if %errorLevel% equ 0 (
    echo ✓ MySQL connection successful without password
    echo Your MySQL root user has no password set
    goto mysql_working
) else (
    echo ✗ Connection failed without password
)

:: Test 3: Test with password prompt
echo.
echo [3/5] Testing connection with password prompt...
echo Please enter your MySQL root password when prompted:
mysql -u root -p -e "SELECT 1;"
if %errorLevel% equ 0 (
    echo ✓ MySQL connection successful with password prompt
    goto mysql_working
) else (
    echo ✗ Connection failed with password prompt
)

:: Test 4: Test with quoted password
echo.
echo [4/5] Testing connection with quoted password...
set /p MYSQL_PASSWORD="Enter MySQL root password: "
mysql -u root -p"%MYSQL_PASSWORD%" -e "SELECT 1;" >nul 2>&1
if %errorLevel% equ 0 (
    echo ✓ MySQL connection successful with quoted password
    goto mysql_working
) else (
    echo ✗ Connection failed with quoted password
)

:: Test 5: Check MySQL service status
echo.
echo [5/5] Checking MySQL service status...
sc query mysql >nul 2>&1
if %errorLevel% equ 0 (
    echo ✓ MySQL service found
    sc query mysql | find "RUNNING" >nul
    if %errorLevel% equ 0 (
        echo ✓ MySQL service is running
    ) else (
        echo ✗ MySQL service is not running
        echo.
        echo Attempting to start MySQL service...
        sc start mysql
        timeout /t 5 /nobreak >nul
        sc query mysql | find "RUNNING" >nul
        if %errorLevel% equ 0 (
            echo ✓ MySQL service started successfully
        ) else (
            echo ✗ Failed to start MySQL service
        )
    )
) else (
    echo ✗ MySQL service not found
    echo Please check if MySQL is properly installed
)

echo.
echo ========================================
echo MySQL Troubleshooting Complete
echo ========================================
echo.
echo If MySQL is still not working, try these solutions:
echo.
echo 1. Reset MySQL root password:
echo    - Stop MySQL service: sc stop mysql
echo    - Start with skip-grant-tables: mysqld --skip-grant-tables
echo    - Connect: mysql -u root
echo    - Reset password: ALTER USER 'root'@'localhost' IDENTIFIED BY 'newpassword';
echo    - Flush privileges: FLUSH PRIVILEGES;
echo    - Restart MySQL service normally
echo.
echo 2. Check MySQL configuration:
echo    - Look for my.ini or my.cnf file
echo    - Ensure bind-address is set correctly
echo.
echo 3. Try connecting with different user:
echo    - Create new user: CREATE USER 'admin'@'localhost' IDENTIFIED BY 'password';
echo    - Grant privileges: GRANT ALL PRIVILEGES ON *.* TO 'admin'@'localhost';
echo.
pause
exit /b 0

:mysql_working
echo.
echo ========================================
echo MySQL Connection Successful!
echo ========================================
echo.
echo You can now proceed with the deployment script.
echo.
pause
exit /b 0
