@echo off
echo ========================================
echo MySQL PATH Configuration Script
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
echo MySQL is installed at: C:\Program Files\MySQL\MySQL Server 8.0\bin
echo Adding MySQL to system PATH...
echo.

:: Add MySQL to system PATH
set MYSQL_PATH=C:\Program Files\MySQL\MySQL Server 8.0\bin

:: Check if MySQL is already in PATH
echo %PATH% | find /i "%MYSQL_PATH%" >nul
if %errorLevel% equ 0 (
    echo ✓ MySQL is already in system PATH
) else (
    echo Adding MySQL to system PATH...
    
    :: Add to system PATH permanently
    setx PATH "%PATH%;%MYSQL_PATH%" /M >nul 2>&1
    
    if %errorLevel% equ 0 (
        echo ✓ MySQL added to system PATH successfully
        echo Note: You may need to restart Command Prompt for changes to take effect
    ) else (
        echo ✗ Failed to add MySQL to system PATH
        echo Please add it manually:
        echo 1. Open System Properties
        echo 2. Go to Environment Variables
        echo 3. Add to PATH: %MYSQL_PATH%
    )
)

echo.
echo [1/4] Testing MySQL client availability...

:: Test MySQL client
"%MYSQL_PATH%\mysql.exe" --version >nul 2>&1
if %errorLevel% equ 0 (
    echo ✓ MySQL client is working
    "%MYSQL_PATH%\mysql.exe" --version
) else (
    echo ✗ MySQL client not found at expected location
    echo Please check if MySQL is properly installed
    pause
    exit /b 1
)

echo.
echo [2/4] Checking MySQL service status...

:: Check MySQL service
sc query mysql >nul 2>&1
if %errorLevel% neq 0 (
    sc query MySQL80 >nul 2>&1
    if %errorLevel% equ 0 (
        set MYSQL_SERVICE=MySQL80
        echo ✓ Found MySQL service: MySQL80
    ) else (
        sc query MySQL57 >nul 2>&1
        if %errorLevel% equ 0 (
            set MYSQL_SERVICE=MySQL57
            echo ✓ Found MySQL service: MySQL57
        ) else (
            echo ✗ MySQL service not found
            echo Please check MySQL installation
            pause
            exit /b 1
        )
    )
) else (
    set MYSQL_SERVICE=mysql
    echo ✓ Found MySQL service: mysql
)

:: Check if service is running
sc query %MYSQL_SERVICE% | find "RUNNING" >nul
if %errorLevel% equ 0 (
    echo ✓ MySQL service is running
) else (
    echo Starting MySQL service...
    sc start %MYSQL_SERVICE%
    timeout /t 10 /nobreak >nul
    
    sc query %MYSQL_SERVICE% | find "RUNNING" >nul
    if %errorLevel% equ 0 (
        echo ✓ MySQL service started successfully
    ) else (
        echo ✗ Failed to start MySQL service
        echo Please start it manually from Services (services.msc)
    )
)

echo.
echo [3/4] Testing MySQL connection...

:: Test connection without password first
"%MYSQL_PATH%\mysql.exe" -u root -e "SELECT 1;" >nul 2>&1
if %errorLevel% equ 0 (
    echo ✓ MySQL connection successful (no password required)
    echo You can proceed with the deployment script
    goto mysql_ready
)

:: Test with password prompt
echo MySQL requires a password. Please enter your root password:
"%MYSQL_PATH%\mysql.exe" -u root -p -e "SELECT 1;"
if %errorLevel% equ 0 (
    echo ✓ MySQL connection successful with password
    goto mysql_ready
) else (
    echo ✗ MySQL connection failed
    echo Please check your root password
)

echo.
echo [4/4] Setting up MySQL for deployment...

:: Get root password for deployment script
echo.
echo For the deployment script to work, we need to know your MySQL root password.
echo.
set /p MYSQL_ROOT_PASSWORD="Enter your MySQL root password: "
if "%MYSQL_ROOT_PASSWORD%"=="" (
    echo ERROR: Root password is required
    pause
    exit /b 1
)

:: Test connection with provided password
"%MYSQL_PATH%\mysql.exe" -u root -p"%MYSQL_ROOT_PASSWORD%" -e "SELECT 1;" >nul 2>&1
if %errorLevel% equ 0 (
    echo ✓ MySQL connection test successful!
) else (
    echo ✗ MySQL connection test failed
    echo Please verify your password and try again
    pause
    exit /b 1
)

:mysql_ready
echo.
echo ========================================
echo MySQL Configuration Complete!
echo ========================================
echo.
echo MySQL Information:
echo - Installation Path: %MYSQL_PATH%
echo - Service Name: %MYSQL_SERVICE%
echo - Root Password: %MYSQL_ROOT_PASSWORD%
echo.
echo You can now run the deployment script:
echo dynamic_deploy_clean.bat
echo.
echo When prompted for MySQL root password, use: %MYSQL_ROOT_PASSWORD%
echo.
pause
exit /b 0
