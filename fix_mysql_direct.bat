@echo off
echo ========================================
echo Direct MySQL Authentication Fix
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
echo This script will fix MySQL authentication using a direct approach.
echo.

set /p CONFIRM="Do you want to fix MySQL authentication? (y/n): "
if /i not "%CONFIRM%"=="y" (
    echo Operation cancelled.
    pause
    exit /b 1
)

echo.
echo [1/3] Stopping MySQL service...

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
echo [2/3] Starting MySQL in safe mode using service...

:: Set MySQL path
set MYSQL_PATH=C:\Program Files\MySQL\MySQL Server 8.0\bin

:: Create a batch file to start MySQL in safe mode
(
echo @echo off
echo cd /d "%MYSQL_PATH%"
echo mysqld.exe --skip-grant-tables --skip-networking --console
) > "%TEMP%\start_mysql_safe.bat"

:: Start MySQL in safe mode
echo Starting MySQL in safe mode...
start /b cmd /c "%TEMP%\start_mysql_safe.bat"

echo Waiting for MySQL to start in safe mode...
timeout /t 15 /nobreak >nul

echo.
echo [3/3] Fixing authentication...

:: Test connection and fix authentication
echo Testing connection and fixing authentication...
"%MYSQL_PATH%\mysql.exe" -u root -e "USE mysql; ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'root123'; FLUSH PRIVILEGES; SELECT 'Authentication fixed' as result;"

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
        echo.
        echo Manual steps required:
        echo 1. Open MySQL Workbench
        echo 2. Connect to localhost:3306
        echo 3. Run: ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'root123';
        echo 4. Run: FLUSH PRIVILEGES;
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
if exist "%TEMP%\start_mysql_safe.bat" del "%TEMP%\start_mysql_safe.bat"

echo.
pause
exit /b 0
