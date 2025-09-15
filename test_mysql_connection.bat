@echo off
echo ========================================
echo MySQL Connection Test Script
echo ========================================

echo.
echo Testing MySQL connection with fixed authentication...
echo.

set MYSQL_PATH=C:\Program Files\MySQL\MySQL Server 8.0\bin

echo [1/3] Testing connection with root123 password...
"%MYSQL_PATH%\mysql.exe" -u root -proot123 -e "SELECT 1;" >nul 2>&1
if %errorLevel% equ 0 (
    echo ✓ MySQL connection successful with password: root123
    echo.
    echo ========================================
    echo MySQL Connection Test Successful!
    echo ========================================
    echo.
    echo MySQL Information:
    echo - Root Password: root123
    echo - Authentication: mysql_native_password
    echo - Connection: Working
    echo.
    echo You can now run the deployment script:
    echo dynamic_deploy_clean.bat
    echo.
    echo When prompted for MySQL root password, use: root123
    goto success
)

echo.
echo [2/3] Testing connection without password...
"%MYSQL_PATH%\mysql.exe" -u root -e "SELECT 1;" >nul 2>&1
if %errorLevel% equ 0 (
    echo ✓ MySQL connection successful without password
    echo.
    echo ========================================
    echo MySQL Connection Test Successful!
    echo ========================================
    echo.
    echo MySQL Information:
    echo - Root Password: (none)
    echo - Authentication: Working
    echo - Connection: Working
    echo.
    echo You can now run the deployment script:
    echo dynamic_deploy_clean.bat
    echo.
    echo When prompted for MySQL root password, leave it empty
    goto success
)

echo.
echo [3/3] Testing connection with manual password entry...
echo Please try entering your password manually:
"%MYSQL_PATH%\mysql.exe" -u root -p -e "SELECT 1;"
if %errorLevel% equ 0 (
    echo ✓ MySQL connection successful with manual password entry
    echo.
    echo ========================================
    echo MySQL Connection Test Successful!
    echo ========================================
    echo.
    echo MySQL is working with manual password entry.
    echo You can now run the deployment script:
    echo dynamic_deploy_clean.bat
    goto success
)

echo.
echo ========================================
echo MySQL Connection Test Failed
echo ========================================
echo.
echo All connection tests failed.
echo Please run the authentication fix script:
echo fix_mysql_auth.bat
echo.
pause
exit /b 1

:success
echo.
pause
exit /b 0
