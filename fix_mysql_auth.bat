@echo off
echo ========================================
echo MySQL Authentication Fix Script
echo ========================================

:: Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This script must be run as Administrator
    echo Right-click and select "Run as administrator"
    pause
    exit /b 1
)

echo.
echo The error indicates a MySQL authentication plugin issue.
echo This script will fix the authentication problem.
echo.

set /p CONFIRM="Do you want to fix MySQL authentication? (y/n): "
if /i not "%CONFIRM%"=="y" (
    echo Operation cancelled.
    pause
    exit /b 0
)

echo.
echo [1/6] Stopping MySQL service...

:: Stop MySQL service
sc stop MySQL80
if %errorLevel% neq 0 (
    sc stop mysql
    if %errorLevel% neq 0 (
        sc stop MySQL57
    )
)

echo Waiting for MySQL to stop...
timeout /t 5 /nobreak >nul

echo.
echo [2/6] Starting MySQL with skip-grant-tables...

:: Set MySQL path
set MYSQL_PATH=C:\Program Files\MySQL\MySQL Server 8.0\bin

:: Start MySQL with skip-grant-tables
echo Starting MySQL in safe mode...
start /b "%MYSQL_PATH%\mysqld.exe" --skip-grant-tables --skip-networking

echo Waiting for MySQL to start in safe mode...
timeout /t 10 /nobreak >nul

echo.
echo [3/6] Connecting to MySQL without password...

:: Test connection without password
"%MYSQL_PATH%\mysql.exe" -u root -e "SELECT 1;" >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Cannot connect to MySQL even in safe mode
    echo Please check MySQL installation
    goto cleanup
)

echo ✓ Connected to MySQL in safe mode

echo.
echo [4/6] Fixing authentication plugin...

:: Create SQL commands to fix authentication
(
echo USE mysql;
echo ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'root123';
echo FLUSH PRIVILEGES;
echo EXIT;
) > fix_auth.sql

:: Execute authentication fix
echo Fixing authentication plugin...
"%MYSQL_PATH%\mysql.exe" -u root < fix_auth.sql

if %errorLevel% equ 0 (
    echo ✓ Authentication plugin fixed successfully!
    echo New password set to: root123
) else (
    echo ✗ Authentication fix failed
    goto cleanup
)

echo.
echo [5/6] Stopping MySQL safe mode...

:: Stop MySQL safe mode
taskkill /f /im mysqld.exe >nul 2>&1
timeout /t 3 /nobreak >nul

echo.
echo [6/6] Starting MySQL service normally...

:: Start MySQL service normally
sc start MySQL80
if %errorLevel% neq 0 (
    sc start mysql
    if %errorLevel% neq 0 (
        sc start MySQL57
    )
)

echo Waiting for MySQL to start normally...
timeout /t 15 /nobreak >nul

:: Test new authentication
echo Testing new authentication...
"%MYSQL_PATH%\mysql.exe" -u root -proot123 -e "SELECT 1;" >nul 2>&1
if %errorLevel% equ 0 (
    echo ✓ MySQL is working with fixed authentication!
    echo.
    echo ========================================
    echo Authentication Fix Complete!
    echo ========================================
    echo.
    echo MySQL Information:
    echo - Root Password: root123
    echo - Authentication: mysql_native_password
    echo - Service Status: Running
    echo.
    echo You can now run the deployment script:
    echo dynamic_deploy_clean.bat
    echo.
    echo When prompted for MySQL root password, use: root123
) else (
    echo ✗ Authentication test failed
    echo Please check MySQL service status manually
)

:: Cleanup
:cleanup
if exist fix_auth.sql del fix_auth.sql

echo.
pause
exit /b 0
