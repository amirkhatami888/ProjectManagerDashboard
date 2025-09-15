@echo off
echo ========================================
echo MySQL Service Configuration Script
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
echo MySQL client is working but service is not found.
echo This script will configure MySQL as a Windows service.
echo.

set /p CONFIRM="Do you want to proceed with MySQL service configuration? (y/n): "
if /i not "%CONFIRM%"=="y" (
    echo Operation cancelled.
    pause
    exit /b 0
)

echo.
echo [1/5] Checking MySQL installation...

:: Check if MySQL is installed
set MYSQL_PATH=C:\Program Files\MySQL\MySQL Server 8.0\bin
if not exist "%MYSQL_PATH%\mysql.exe" (
    echo ERROR: MySQL not found at expected location
    echo Please check MySQL installation
    pause
    exit /b 1
)

echo ✓ MySQL found at: %MYSQL_PATH%

echo.
echo [2/5] Checking for existing MySQL services...

:: Check for various MySQL service names
sc query mysql >nul 2>&1
if %errorLevel% equ 0 (
    echo ✓ Found MySQL service: mysql
    set MYSQL_SERVICE=mysql
    goto service_found
)

sc query MySQL80 >nul 2>&1
if %errorLevel% equ 0 (
    echo ✓ Found MySQL service: MySQL80
    set MYSQL_SERVICE=MySQL80
    goto service_found
)

sc query MySQL57 >nul 2>&1
if %errorLevel% equ 0 (
    echo ✓ Found MySQL service: MySQL57
    set MYSQL_SERVICE=MySQL57
    goto service_found
)

sc query MySQL8.0 >nul 2>&1
if %errorLevel% equ 0 (
    echo ✓ Found MySQL service: MySQL8.0
    set MYSQL_SERVICE=MySQL8.0
    goto service_found
)

echo ✗ No MySQL service found
goto create_service

:service_found
echo.
echo [3/5] Checking service status...

sc query %MYSQL_SERVICE% | find "RUNNING" >nul
if %errorLevel% equ 0 (
    echo ✓ MySQL service is running
    goto test_connection
) else (
    echo Starting MySQL service...
    sc start %MYSQL_SERVICE%
    timeout /t 10 /nobreak >nul
    
    sc query %MYSQL_SERVICE% | find "RUNNING" >nul
    if %errorLevel% equ 0 (
        echo ✓ MySQL service started successfully
        goto test_connection
    ) else (
        echo ✗ Failed to start MySQL service
        echo Please check service configuration manually
        pause
        exit /b 1
    )
)

:create_service
echo.
echo [3/5] Creating MySQL service...

:: Get MySQL root password
echo.
echo To create the MySQL service, we need your root password.
set /p MYSQL_ROOT_PASSWORD="Enter MySQL root password: "
if "%MYSQL_ROOT_PASSWORD%"=="" (
    echo ERROR: Root password is required
    pause
    exit /b 1
)

:: Test connection first
echo Testing MySQL connection...
"%MYSQL_PATH%\mysql.exe" -u root -p"%MYSQL_ROOT_PASSWORD%" -e "SELECT 1;" >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Cannot connect to MySQL with provided password
    echo Please check your password and try again
    pause
    exit /b 1
)

echo ✓ MySQL connection successful

:: Create MySQL service
echo Creating MySQL service...
"%MYSQL_PATH%\mysqld.exe" --install MySQL80 --defaults-file="C:\Program Files\MySQL\MySQL Server 8.0\my.ini"

if %errorLevel% equ 0 (
    echo ✓ MySQL service created successfully
    set MYSQL_SERVICE=MySQL80
) else (
    echo ✗ Failed to create MySQL service
    echo Trying alternative method...
    
    :: Try with different service name
    "%MYSQL_PATH%\mysqld.exe" --install mysql --defaults-file="C:\Program Files\MySQL\MySQL Server 8.0\my.ini"
    if %errorLevel% equ 0 (
        echo ✓ MySQL service created successfully
        set MYSQL_SERVICE=mysql
    ) else (
        echo ✗ Failed to create MySQL service with both methods
        echo Please check MySQL configuration files
        pause
        exit /b 1
    )
)

:: Start the service
echo Starting MySQL service...
sc start %MYSQL_SERVICE%
timeout /t 15 /nobreak >nul

sc query %MYSQL_SERVICE% | find "RUNNING" >nul
if %errorLevel% equ 0 (
    echo ✓ MySQL service started successfully
) else (
    echo ✗ Failed to start MySQL service
    echo Please check service configuration manually
    pause
    exit /b 1
)

:test_connection
echo.
echo [4/5] Testing MySQL connection...

:: Test connection
"%MYSQL_PATH%\mysql.exe" -u root -p"%MYSQL_ROOT_PASSWORD%" -e "SELECT 1;" >nul 2>&1
if %errorLevel% equ 0 (
    echo ✓ MySQL connection test successful!
) else (
    echo ✗ MySQL connection test failed
    echo Please check your password and service status
    pause
    exit /b 1
)

echo.
echo [5/5] Configuring MySQL for deployment...

:: Set service to auto-start
echo Configuring MySQL service to start automatically...
sc config %MYSQL_SERVICE% start= auto

if %errorLevel% equ 0 (
    echo ✓ MySQL service configured for auto-start
) else (
    echo Warning: Could not configure auto-start
)

echo.
echo ========================================
echo MySQL Service Configuration Complete!
echo ========================================
echo.
echo MySQL Information:
echo - Service Name: %MYSQL_SERVICE%
echo - Service Status: Running
echo - Auto-start: Enabled
echo - Root Password: %MYSQL_ROOT_PASSWORD%
echo.
echo You can now run the deployment script:
echo dynamic_deploy_clean.bat
echo.
echo When prompted for MySQL root password, use: %MYSQL_ROOT_PASSWORD%
echo.
pause
exit /b 0
