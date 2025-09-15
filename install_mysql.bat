@echo off
echo ========================================
echo MySQL Installation Script for Windows
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
echo This script will install MySQL Server on Windows
echo.

set /p CONFIRM="Do you want to proceed with MySQL installation? (y/n): "
if /i not "%CONFIRM%"=="y" (
    echo Installation cancelled.
    pause
    exit /b 0
)

echo.
echo [1/6] Downloading MySQL Installer...

:: Create temp directory
if not exist "%TEMP%\mysql_install" mkdir "%TEMP%\mysql_install"
cd /d "%TEMP%\mysql_install"

:: Download MySQL Installer (Community Server)
echo Downloading MySQL Installer...
curl -L -o mysql-installer-community.msi "https://dev.mysql.com/get/Downloads/MySQLInstaller/mysql-installer-community-8.0.35.0.msi"

if %errorLevel% neq 0 (
    echo ERROR: Failed to download MySQL Installer
    echo Please download manually from: https://dev.mysql.com/downloads/installer/
    pause
    exit /b 1
)

echo ✓ MySQL Installer downloaded successfully

echo.
echo [2/6] Installing MySQL Server...

:: Install MySQL Server silently
echo Installing MySQL Server (this may take several minutes)...
msiexec /i mysql-installer-community.msi /quiet /norestart

if %errorLevel% neq 0 (
    echo ERROR: MySQL installation failed
    echo Please try manual installation from the downloaded file
    pause
    exit /b 1
)

echo ✓ MySQL Server installed successfully

echo.
echo [3/6] Configuring MySQL Service...

:: Wait for MySQL service to be created
echo Waiting for MySQL service to be created...
timeout /t 10 /nobreak >nul

:: Check if MySQL service exists
sc query mysql >nul 2>&1
if %errorLevel% neq 0 (
    echo Warning: MySQL service not found, trying alternative service names...
    
    :: Try common MySQL service names
    sc query MySQL80 >nul 2>&1
    if %errorLevel% equ 0 (
        echo ✓ Found MySQL service: MySQL80
        set MYSQL_SERVICE=MySQL80
    ) else (
        sc query MySQL57 >nul 2>&1
        if %errorLevel% equ 0 (
            echo ✓ Found MySQL service: MySQL57
            set MYSQL_SERVICE=MySQL57
        ) else (
            echo ERROR: MySQL service not found
            echo Please check MySQL installation manually
            pause
            exit /b 1
        )
    )
) else (
    echo ✓ Found MySQL service: mysql
    set MYSQL_SERVICE=mysql
)

echo.
echo [4/6] Starting MySQL Service...

:: Start MySQL service
sc start %MYSQL_SERVICE%
if %errorLevel% neq 0 (
    echo Warning: Could not start MySQL service automatically
    echo Please start it manually from Services (services.msc)
)

:: Wait for service to start
echo Waiting for MySQL service to start...
timeout /t 15 /nobreak >nul

:: Check if service is running
sc query %MYSQL_SERVICE% | find "RUNNING" >nul
if %errorLevel% equ 0 (
    echo ✓ MySQL service is running
) else (
    echo Warning: MySQL service might not be running
    echo Please check Services (services.msc) and start MySQL manually
)

echo.
echo [5/6] Setting up MySQL Root Password...

:: Get root password from user
echo.
echo IMPORTANT: You need to set a root password for MySQL
echo This password will be used by the deployment script
echo.
set /p MYSQL_ROOT_PASSWORD="Enter MySQL root password: "
if "%MYSQL_ROOT_PASSWORD%"=="" (
    echo ERROR: Root password is required
    pause
    exit /b 1
)

:: Try to connect and set password
echo Setting up MySQL root password...
mysql -u root -e "ALTER USER 'root'@'localhost' IDENTIFIED BY '%MYSQL_ROOT_PASSWORD%';" 2>nul
if %errorLevel% neq 0 (
    echo Warning: Could not set password automatically
    echo You may need to set it manually using MySQL Workbench or command line
) else (
    echo ✓ MySQL root password set successfully
)

echo.
echo [6/6] Testing MySQL Connection...

:: Test connection with new password
mysql -u root -p"%MYSQL_ROOT_PASSWORD%" -e "SELECT 1;" >nul 2>&1
if %errorLevel% equ 0 (
    echo ✓ MySQL connection test successful!
) else (
    echo Warning: MySQL connection test failed
    echo Please check the password and try again
)

:: Cleanup
echo.
echo Cleaning up installation files...
cd /d "%TEMP%"
rmdir /s /q mysql_install >nul 2>&1

echo.
echo ========================================
echo MySQL Installation Complete!
echo ========================================
echo.
echo MySQL Server Information:
echo - Service Name: %MYSQL_SERVICE%
echo - Root Password: %MYSQL_ROOT_PASSWORD%
echo - Port: 3306 (default)
echo.
echo You can now run the deployment script with this password:
echo Password: %MYSQL_ROOT_PASSWORD%
echo.
echo Next steps:
echo 1. Run: dynamic_deploy_clean.bat
echo 2. Use the password above when prompted
echo.
pause
exit /b 0
