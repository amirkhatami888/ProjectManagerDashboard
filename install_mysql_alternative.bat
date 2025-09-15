@echo off
echo ========================================
echo MySQL Alternative Installation Methods
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
echo Choose your preferred MySQL installation method:
echo.
echo [1] Install via Chocolatey (if available)
echo [2] Manual download and installation
echo [3] Install MySQL using Windows Package Manager (winget)
echo.

set /p CHOICE="Enter your choice (1-3): "

if "%CHOICE%"=="1" goto chocolatey_install
if "%CHOICE%"=="2" goto manual_install
if "%CHOICE%"=="3" goto winget_install

echo Invalid choice. Please run the script again.
pause
exit /b 1

:chocolatey_install
echo.
echo [1/3] Installing MySQL via Chocolatey...

:: Check if Chocolatey is installed
choco --version >nul 2>&1
if %errorLevel% neq 0 (
    echo Chocolatey is not installed. Installing Chocolatey first...
    powershell -Command "Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))"
    
    if %errorLevel% neq 0 (
        echo ERROR: Failed to install Chocolatey
        goto manual_install
    )
)

echo Installing MySQL Server...
choco install mysql -y

if %errorLevel% equ 0 (
    echo ✓ MySQL installed successfully via Chocolatey
    goto mysql_configure
) else (
    echo ERROR: MySQL installation failed via Chocolatey
    goto manual_install
)

:winget_install
echo.
echo [1/3] Installing MySQL via Windows Package Manager...

:: Check if winget is available
winget --version >nul 2>&1
if %errorLevel% neq 0 (
    echo Windows Package Manager (winget) is not available
    echo Please use Windows 10 version 1709 or later, or install App Installer
    goto manual_install
)

echo Installing MySQL Server...
winget install Oracle.MySQL

if %errorLevel% equ 0 (
    echo ✓ MySQL installed successfully via winget
    goto mysql_configure
) else (
    echo ERROR: MySQL installation failed via winget
    goto manual_install
)

:manual_install
echo.
echo [1/3] Manual MySQL Installation Instructions
echo.
echo Please follow these steps to install MySQL manually:
echo.
echo 1. Download MySQL Installer:
echo    - Go to: https://dev.mysql.com/downloads/installer/
echo    - Download: mysql-installer-community.msi
echo.
echo 2. Run the installer:
echo    - Double-click the downloaded .msi file
echo    - Choose "Developer Default" setup type
echo    - Follow the installation wizard
echo    - Set a root password when prompted
echo    - Ensure MySQL Server is configured as a Windows service
echo.
echo 3. After installation, return here and press any key to continue...
echo.
pause

:mysql_configure
echo.
echo [2/3] Configuring MySQL...

:: Wait for MySQL to be available
echo Waiting for MySQL to be available...
timeout /t 10 /nobreak >nul

:: Check MySQL service
sc query mysql >nul 2>&1
if %errorLevel% neq 0 (
    sc query MySQL80 >nul 2>&1
    if %errorLevel% equ 0 (
        set MYSQL_SERVICE=MySQL80
    ) else (
        sc query MySQL57 >nul 2>&1
        if %errorLevel% equ 0 (
            set MYSQL_SERVICE=MySQL57
        ) else (
            echo ERROR: MySQL service not found
            echo Please ensure MySQL is properly installed
            pause
            exit /b 1
        )
    )
) else (
    set MYSQL_SERVICE=mysql
)

:: Start MySQL service
echo Starting MySQL service...
sc start %MYSQL_SERVICE%
timeout /t 10 /nobreak >nul

echo.
echo [3/3] Testing MySQL Connection...

:: Test connection
mysql --version >nul 2>&1
if %errorLevel% neq 0 (
    echo Warning: MySQL client not found in PATH
    echo Please add MySQL bin directory to your system PATH
    echo Usually located at: C:\Program Files\MySQL\MySQL Server 8.0\bin
)

:: Get root password
echo.
echo Please enter your MySQL root password:
set /p MYSQL_ROOT_PASSWORD="MySQL root password: "

:: Test connection with password
mysql -u root -p"%MYSQL_ROOT_PASSWORD%" -e "SELECT 1;" >nul 2>&1
if %errorLevel% equ 0 (
    echo ✓ MySQL connection successful!
) else (
    echo ✗ MySQL connection failed
    echo Please check your password and try again
    pause
    exit /b 1
)

echo.
echo ========================================
echo MySQL Installation Complete!
echo ========================================
echo.
echo MySQL is now ready for use with the deployment script.
echo Root Password: %MYSQL_ROOT_PASSWORD%
echo.
echo You can now run: dynamic_deploy_clean.bat
echo.
pause
exit /b 0
