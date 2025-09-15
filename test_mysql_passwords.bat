@echo off
echo ========================================
echo MySQL Password Testing Script
echo ========================================

echo.
echo This script will test common MySQL root passwords.
echo.

set MYSQL_PATH=C:\Program Files\MySQL\MySQL Server 8.0\bin

echo [1/4] Testing connection without password...
"%MYSQL_PATH%\mysql.exe" -u root -e "SELECT 1;" >nul 2>&1
if %errorLevel% equ 0 (
    echo ✓ MySQL connection successful without password
    echo Your MySQL root user has no password set
    goto mysql_working
)

echo.
echo [2/4] Testing common passwords...

:: Test common passwords
set PASSWORDS=root admin password 123456 mysql root123 admin123

for %%p in (%PASSWORDS%) do (
    echo Testing password: %%p
    "%MYSQL_PATH%\mysql.exe" -u root -p%%p -e "SELECT 1;" >nul 2>&1
    if %errorLevel% equ 0 (
        echo ✓ MySQL connection successful with password: %%p
        set WORKING_PASSWORD=%%p
        goto mysql_working
    )
)

echo.
echo [3/4] Testing with password prompt...
echo Please try entering your password manually:
"%MYSQL_PATH%\mysql.exe" -u root -p -e "SELECT 1;"
if %errorLevel% equ 0 (
    echo ✓ MySQL connection successful with manual password entry
    goto mysql_working
)

echo.
echo [4/4] All password tests failed

echo.
echo ========================================
echo MySQL Password Test Results
echo ========================================
echo.
echo None of the common passwords worked.
echo Your MySQL root password is not one of the common defaults.
echo.
echo Solutions:
echo 1. Try to remember your original password
echo 2. Run reset_mysql_root_password.bat to reset the password
echo 3. Check if you have a password file or documentation
echo.
echo If you want to reset the password, run:
echo reset_mysql_root_password.bat
echo.
pause
exit /b 1

:mysql_working
echo.
echo ========================================
echo MySQL Connection Successful!
echo ========================================
echo.
if defined WORKING_PASSWORD (
    echo Working password: %WORKING_PASSWORD%
    echo.
    echo You can now run the deployment script:
    echo dynamic_deploy_clean.bat
    echo.
    echo When prompted for MySQL root password, use: %WORKING_PASSWORD%
) else (
    echo MySQL is working with manual password entry.
    echo You can now run the deployment script:
    echo dynamic_deploy_clean.bat
)
echo.
pause
exit /b 0
