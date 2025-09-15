@echo off
echo ========================================
echo MySQL Root Password Reset Tool
echo ========================================

echo.
echo WARNING: This will reset your MySQL root password!
echo Make sure you have administrator privileges.
echo.

set /p CONFIRM="Do you want to continue? (y/n): "
if /i not "%CONFIRM%"=="y" (
    echo Operation cancelled.
    pause
    exit /b 0
)

echo.
echo [1/4] Stopping MySQL service...
sc stop mysql
if %errorLevel% neq 0 (
    echo Warning: Could not stop MySQL service (might not be running)
)

echo.
echo [2/4] Starting MySQL with skip-grant-tables...
echo This allows connection without password authentication.
echo.
echo Starting MySQL in background...
start /b mysqld --skip-grant-tables --skip-networking

echo Waiting for MySQL to start...
timeout /t 10 /nobreak >nul

echo.
echo [3/4] Resetting root password...
set /p NEW_PASSWORD="Enter new MySQL root password: "
if "%NEW_PASSWORD%"=="" (
    echo ERROR: Password cannot be empty
    goto cleanup
)

:: Create SQL commands file
(
echo USE mysql;
echo ALTER USER 'root'@'localhost' IDENTIFIED BY '%NEW_PASSWORD%';
echo FLUSH PRIVILEGES;
echo EXIT;
) > reset_password.sql

:: Execute password reset
mysql -u root < reset_password.sql

if %errorLevel% equ 0 (
    echo ✓ Password reset successful!
) else (
    echo ✗ Password reset failed
    goto cleanup
)

echo.
echo [4/4] Restarting MySQL service normally...
taskkill /f /im mysqld.exe >nul 2>&1
timeout /t 3 /nobreak >nul
sc start mysql

echo Waiting for MySQL to start normally...
timeout /t 10 /nobreak >nul

:: Test new password
echo.
echo Testing new password...
mysql -u root -p"%NEW_PASSWORD%" -e "SELECT 1;" >nul 2>&1
if %errorLevel% equ 0 (
    echo ✓ MySQL is working with new password!
    echo.
    echo You can now use this password in the deployment script:
    echo Password: %NEW_PASSWORD%
) else (
    echo ✗ Password test failed
    echo Please check MySQL service status manually
)

:: Cleanup
:cleanup
if exist reset_password.sql del reset_password.sql

echo.
echo ========================================
echo Password Reset Complete
echo ========================================
echo.
pause
exit /b 0
