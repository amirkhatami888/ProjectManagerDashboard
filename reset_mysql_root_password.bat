@echo off
echo ========================================
echo MySQL Root Password Reset Script
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
echo This script will reset your MySQL root password.
echo The MySQL service is running but connection is failing.
echo.

set /p CONFIRM="Do you want to reset the MySQL root password? (y/n): "
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
    echo Warning: Could not stop MySQL80 service
    echo Trying alternative service names...
    
    sc stop mysql
    if %errorLevel% neq 0 (
        sc stop MySQL57
        if %errorLevel% neq 0 (
            echo Warning: Could not stop MySQL service automatically
            echo Please stop it manually from Services (services.msc)
            echo Press any key when MySQL service is stopped...
            pause
        )
    )
)

echo Waiting for MySQL to stop...
timeout /t 5 /nobreak >nul

echo.
echo [2/6] Starting MySQL with skip-grant-tables...

:: Set MySQL path
set MYSQL_PATH=C:\Program Files\MySQL\MySQL Server 8.0\bin

:: Start MySQL with skip-grant-tables
echo Starting MySQL in safe mode (skip-grant-tables)...
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
echo [4/6] Resetting root password...

:: Get new password
echo.
echo Please enter a new password for MySQL root user:
set /p NEW_PASSWORD="New MySQL root password: "
if "%NEW_PASSWORD%"=="" (
    echo ERROR: Password cannot be empty
    goto cleanup
)

:: Create SQL commands file
(
echo USE mysql;
echo ALTER USER 'root'@'localhost' IDENTIFIED BY '%NEW_PASSWORD%';
echo FLUSH PRIVILEGES;
echo EXIT;
) > reset_password.sql

:: Execute password reset
echo Resetting password...
"%MYSQL_PATH%\mysql.exe" -u root < reset_password.sql

if %errorLevel% equ 0 (
    echo ✓ Password reset successful!
) else (
    echo ✗ Password reset failed
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

:: Test new password
echo Testing new password...
"%MYSQL_PATH%\mysql.exe" -u root -p"%NEW_PASSWORD%" -e "SELECT 1;" >nul 2>&1
if %errorLevel% equ 0 (
    echo ✓ MySQL is working with new password!
    echo.
    echo ========================================
    echo Password Reset Complete!
    echo ========================================
    echo.
    echo MySQL Information:
    echo - Root Password: %NEW_PASSWORD%
    echo - Service Status: Running
    echo.
    echo You can now run the deployment script:
    echo dynamic_deploy_clean.bat
    echo.
    echo When prompted for MySQL root password, use: %NEW_PASSWORD%
) else (
    echo ✗ Password test failed
    echo Please check MySQL service status manually
)

:: Cleanup
:cleanup
if exist reset_password.sql del reset_password.sql

echo.
pause
exit /b 0
