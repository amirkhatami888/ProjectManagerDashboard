@echo off
echo ========================================
echo Simple MySQL Startup Script
echo ========================================

echo.
echo This script will start MySQL manually for testing.
echo.

:: Set MySQL path
set MYSQL_PATH=C:\Program Files\MySQL\MySQL Server 8.0\bin

echo MySQL Path: %MYSQL_PATH%

:: Check if MySQL is installed
if not exist "%MYSQL_PATH%\mysqld.exe" (
    echo ERROR: MySQL not found at expected location
    echo Please check MySQL installation
    pause
    exit /b 1
)

echo ✓ MySQL found

:: Kill any existing MySQL processes
echo Stopping any existing MySQL processes...
taskkill /f /im mysqld.exe >nul 2>&1
timeout /t 2 /nobreak >nul

:: Start MySQL manually
echo Starting MySQL manually...
cd /d "%MYSQL_PATH%"
start /b mysqld.exe --console

echo Waiting for MySQL to start...
timeout /t 10 /nobreak >nul

echo.
echo ========================================
echo MySQL Started Manually
echo ========================================
echo.
echo MySQL is now running manually.
echo.
echo To test the connection, open another Command Prompt and run:
echo cd /d "%MYSQL_PATH%"
echo mysql.exe -u root -p
echo.
echo If you get the authentication error, try:
echo mysql.exe -u root
echo.
echo To stop MySQL, run:
echo taskkill /f /im mysqld.exe
echo.
echo Press any key to continue...
pause

:: Test connection
echo.
echo Testing MySQL connection...
mysql.exe -u root -e "SELECT 1;" >nul 2>&1
if %errorLevel% equ 0 (
    echo ✓ MySQL connection successful without password
    echo.
    echo You can now run the deployment script:
    echo dynamic_deploy_clean.bat
    echo.
    echo When prompted for MySQL root password, leave it empty
) else (
    echo ✗ MySQL connection failed
    echo.
    echo Try running the authentication fix script:
    echo fix_mysql_manual.bat
)

echo.
pause
exit /b 0
