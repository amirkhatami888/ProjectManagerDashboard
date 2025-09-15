@echo off
echo ========================================
echo Manual MySQL Authentication Fix
echo ========================================

echo.
echo This script will manually start MySQL and fix authentication.
echo.

set /p CONFIRM="Do you want to proceed? (y/n): "
if /i not "%CONFIRM%"=="y" (
    echo Operation cancelled.
    pause
    exit /b 0
)

echo.
echo [1/4] Setting up MySQL paths...

:: Set MySQL paths
set MYSQL_PATH=C:\Program Files\MySQL\MySQL Server 8.0\bin
set MYSQL_DATA=C:\ProgramData\MySQL\MySQL Server 8.0\Data

echo MySQL Path: %MYSQL_PATH%
echo MySQL Data: %MYSQL_DATA%

:: Check if MySQL is installed
if not exist "%MYSQL_PATH%\mysqld.exe" (
    echo ERROR: MySQL not found at expected location
    echo Please check MySQL installation
    pause
    exit /b 1
)

echo ✓ MySQL found

:: Check if data directory exists
if not exist "%MYSQL_DATA%" (
    echo Creating MySQL data directory...
    mkdir "%MYSQL_DATA%" 2>nul
    if not exist "%MYSQL_DATA%" (
        echo ERROR: Cannot create data directory: %MYSQL_DATA%
        echo Please check permissions or create manually
        pause
        exit /b 1
    )
    echo ✓ Data directory created
) else (
    echo ✓ Data directory exists
)

echo.
echo [2/4] Starting MySQL manually in safe mode...

:: Kill any existing MySQL processes
echo Stopping any existing MySQL processes...
taskkill /f /im mysqld.exe >nul 2>&1
timeout /t 2 /nobreak >nul

:: Start MySQL manually in safe mode
echo Starting MySQL in safe mode...
cd /d "%MYSQL_PATH%"
start /b mysqld.exe --skip-grant-tables --skip-networking --datadir="%MYSQL_DATA%" --console

echo Waiting for MySQL to start...
timeout /t 15 /nobreak >nul

echo.
echo [3/4] Testing connection and fixing authentication...

:: Test connection without password
echo Testing connection without password...
mysql.exe -u root -e "SELECT 1;" >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Cannot connect to MySQL even in safe mode
    echo Please check MySQL installation
    goto cleanup
)

echo ✓ Connected to MySQL in safe mode

:: Fix authentication
echo Fixing authentication plugin...
mysql.exe -u root -e "USE mysql; ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'root123'; FLUSH PRIVILEGES; SELECT 'Authentication fixed' as result;"

if %errorLevel% equ 0 (
    echo ✓ Authentication fixed successfully!
    echo New password set to: root123
) else (
    echo ✗ Authentication fix failed
    echo Trying alternative method...
    
    :: Try alternative method
    mysql.exe -u root -e "USE mysql; UPDATE user SET authentication_string=PASSWORD('root123'), plugin='mysql_native_password' WHERE User='root' AND Host='localhost'; FLUSH PRIVILEGES; SELECT 'Alternative fix applied' as result;"
    
    if %errorLevel% equ 0 (
        echo ✓ Alternative authentication fix successful!
    ) else (
        echo ✗ All authentication fixes failed
        echo.
        echo Manual steps required:
        echo 1. Open Command Prompt as Administrator
        echo 2. Navigate to: %MYSQL_PATH%
        echo 3. Run: mysql.exe -u root
        echo 4. Run: USE mysql;
        echo 5. Run: ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'root123';
        echo 6. Run: FLUSH PRIVILEGES;
        echo 7. Run: EXIT;
        goto cleanup
    )
)

echo.
echo [4/4] Stopping MySQL and testing...

:: Stop MySQL
echo Stopping MySQL...
taskkill /f /im mysqld.exe >nul 2>&1
timeout /t 3 /nobreak >nul

:: Start MySQL normally
echo Starting MySQL normally...
start /b mysqld.exe --datadir="%MYSQL_DATA%" --console

echo Waiting for MySQL to start normally...
timeout /t 15 /nobreak >nul

:: Test new authentication
echo Testing new authentication...
mysql.exe -u root -proot123 -e "SELECT 1;" >nul 2>&1
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
    echo - Status: Running manually
    echo.
    echo You can now run the deployment script:
    echo dynamic_deploy_clean.bat
    echo.
    echo When prompted for MySQL root password, use: root123
) else (
    echo ✗ Authentication test failed
    echo Please check MySQL status manually
)

:cleanup
echo.
echo ========================================
echo Manual Fix Complete
echo ========================================
echo.
echo If MySQL is still not working, try these manual steps:
echo.
echo 1. Open Command Prompt as Administrator
echo 2. Navigate to: %MYSQL_PATH%
echo 3. Run: mysqld.exe --skip-grant-tables --skip-networking --datadir="%MYSQL_DATA%" --console
echo 4. Open another Command Prompt
echo 5. Navigate to: %MYSQL_PATH%
echo 6. Run: mysql.exe -u root
echo 7. Run these SQL commands:
echo    USE mysql;
echo    ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'root123';
echo    FLUSH PRIVILEGES;
echo    EXIT;
echo 8. Stop the first Command Prompt (Ctrl+C)
echo 9. Start MySQL normally: mysqld.exe --datadir="%MYSQL_DATA%" --console
echo.
pause
exit /b 0
