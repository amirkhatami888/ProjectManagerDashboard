@echo off
echo ========================================
echo Manual MySQL Startup Script
echo ========================================

echo.
echo This script will start MySQL manually if the service is not working.
echo.

set /p CONFIRM="Do you want to start MySQL manually? (y/n): "
if /i not "%CONFIRM%"=="y" (
    echo Operation cancelled.
    pause
    exit /b 0
)

echo.
echo [1/3] Starting MySQL manually...

:: Set MySQL path
set MYSQL_PATH=C:\Program Files\MySQL\MySQL Server 8.0\bin

:: Check if MySQL is installed
if not exist "%MYSQL_PATH%\mysqld.exe" (
    echo ERROR: MySQL not found at expected location
    echo Please check MySQL installation
    pause
    exit /b 1
)

echo ✓ MySQL found at: %MYSQL_PATH%

:: Get MySQL root password
echo.
echo Please enter your MySQL root password:
set /p MYSQL_ROOT_PASSWORD="MySQL root password: "
if "%MYSQL_ROOT_PASSWORD%"=="" (
    echo ERROR: Root password is required
    pause
    exit /b 1
)

:: Start MySQL in background
echo Starting MySQL server...
start /b "%MYSQL_PATH%\mysqld.exe" --console

:: Wait for MySQL to start
echo Waiting for MySQL to start...
timeout /t 10 /nobreak >nul

echo.
echo [2/3] Testing MySQL connection...

:: Test connection
"%MYSQL_PATH%\mysql.exe" -u root -p"%MYSQL_ROOT_PASSWORD%" -e "SELECT 1;" >nul 2>&1
if %errorLevel% equ 0 (
    echo ✓ MySQL connection successful!
) else (
    echo ✗ MySQL connection failed
    echo Please check your password and try again
    pause
    exit /b 1
)

echo.
echo [3/3] MySQL is now running manually

echo.
echo ========================================
echo MySQL Manual Startup Complete!
echo ========================================
echo.
echo MySQL Information:
echo - Status: Running manually
echo - Root Password: %MYSQL_ROOT_PASSWORD%
echo - Port: 3306 (default)
echo.
echo IMPORTANT: MySQL is running in the background.
echo To stop it, you may need to kill the mysqld.exe process.
echo.
echo You can now run the deployment script:
echo dynamic_deploy_clean.bat
echo.
echo When prompted for MySQL root password, use: %MYSQL_ROOT_PASSWORD%
echo.
pause
exit /b 0
