@echo off
echo ========================================
echo Simple MySQL Authentication Fix
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
echo This script will fix MySQL authentication using a simpler method.
echo.

set /p CONFIRM="Do you want to fix MySQL authentication? (y/n): "
if /i not "%CONFIRM%"=="y" (
    echo Operation cancelled.
    pause
    exit /b 0
)

echo.
echo [1/4] Stopping MySQL service...

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
echo [2/4] Creating MySQL configuration file...

:: Set MySQL path
set MYSQL_PATH=C:\Program Files\MySQL\MySQL Server 8.0\bin
set MYSQL_DATA=C:\ProgramData\MySQL\MySQL Server 8.0\Data

:: Create a temporary my.ini file for safe mode
(
echo [mysqld]
echo skip-grant-tables
echo skip-networking
echo port=3306
echo datadir=%MYSQL_DATA%
echo ) > "%TEMP%\my_safe.ini"

echo ✓ Temporary configuration file created

echo.
echo [3/4] Starting MySQL in safe mode...

:: Start MySQL with the safe configuration
echo Starting MySQL with safe configuration...
start /b "%MYSQL_PATH%\mysqld.exe" --defaults-file="%TEMP%\my_safe.ini"

echo Waiting for MySQL to start in safe mode...
timeout /t 15 /nobreak >nul

echo.
echo [4/4] Fixing authentication and testing...

:: Test connection and fix authentication
echo Testing connection and fixing authentication...
"%MYSQL_PATH%\mysql.exe" -u root -e "USE mysql; ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'root123'; FLUSH PRIVILEGES; SELECT 'Authentication fixed successfully' as result;"

if %errorLevel% equ 0 (
    echo ✓ Authentication fixed successfully!
    echo New password set to: root123
) else (
    echo ✗ Authentication fix failed
    echo Trying alternative method...
    
    :: Try alternative method
    echo Trying alternative authentication fix...
    "%MYSQL_PATH%\mysql.exe" -u root -e "UPDATE mysql.user SET authentication_string=PASSWORD('root123'), plugin='mysql_native_password' WHERE User='root' AND Host='localhost'; FLUSH PRIVILEGES; SELECT 'Alternative fix applied' as result;"
    
    if %errorLevel% equ 0 (
        echo ✓ Alternative authentication fix successful!
    ) else (
        echo ✗ All authentication fixes failed
        goto cleanup
    )
)

:: Stop MySQL safe mode
echo Stopping MySQL safe mode...
taskkill /f /im mysqld.exe >nul 2>&1
timeout /t 3 /nobreak >nul

:: Start MySQL service normally
echo Starting MySQL service normally...
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
if exist "%TEMP%\my_safe.ini" del "%TEMP%\my_safe.ini"

echo.
pause
exit /b 0
