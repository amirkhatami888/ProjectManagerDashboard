@echo off
echo ========================================
echo Check Nginx Configuration
echo ========================================

echo.
echo This script will check the Nginx configuration for common issues.
echo.

echo [1/5] Checking Nginx installation...

:: Check if Nginx executable exists
if not exist "nginx\nginx.exe" (
    echo ERROR: nginx.exe not found at nginx\nginx.exe
    pause
    exit /b 1
)

echo ✓ nginx.exe found

echo.
echo [2/5] Checking configuration file...

:: Check if nginx.conf exists
if not exist "nginx\conf\nginx.conf" (
    echo ERROR: nginx.conf not found at nginx\conf\nginx.conf
    pause
    exit /b 1
)

echo ✓ nginx.conf found

echo.
echo [3/5] Testing configuration syntax...

:: Test Nginx configuration
echo Testing Nginx configuration syntax...
nginx\nginx.exe -t
if %errorLevel% neq 0 (
    echo ERROR: Nginx configuration syntax error
    echo.
    echo Please check the nginx.conf file for syntax errors
    echo Common issues:
    echo - Missing semicolons
    echo - Incorrect brackets
    echo - Invalid directives
    echo.
    echo Configuration file location: nginx\conf\nginx.conf
    pause
    exit /b 1
)

echo ✓ Nginx configuration syntax is valid

echo.
echo [4/5] Checking configuration content...

:: Check for common configuration issues
echo Checking for common configuration issues...

:: Check if server_name is set correctly
findstr /i "server_name" nginx\conf\nginx.conf >nul
if %errorLevel% neq 0 (
    echo WARNING: server_name directive not found
) else (
    echo ✓ server_name directive found
)

:: Check if proxy_pass is set correctly
findstr /i "proxy_pass" nginx\conf\nginx.conf >nul
if %errorLevel% neq 0 (
    echo WARNING: proxy_pass directive not found
) else (
    echo ✓ proxy_pass directive found
)

:: Check if listen directive is set
findstr /i "listen" nginx\conf\nginx.conf >nul
if %errorLevel% neq 0 (
    echo WARNING: listen directive not found
) else (
    echo ✓ listen directive found
)

echo.
echo [5/5] Checking file paths in configuration...

:: Check if static files path exists
findstr /i "staticfiles" nginx\conf\nginx.conf >nul
if %errorLevel% equ 0 (
    if not exist "staticfiles" (
        echo WARNING: staticfiles directory not found
        echo Creating staticfiles directory...
        mkdir staticfiles
        echo ✓ staticfiles directory created
    ) else (
        echo ✓ staticfiles directory exists
    )
)

:: Check if media directory exists
findstr /i "media" nginx\conf\nginx.conf >nul
if %errorLevel% equ 0 (
    if not exist "media" (
        echo WARNING: media directory not found
        echo Creating media directory...
        mkdir media
        echo ✓ media directory created
    ) else (
        echo ✓ media directory exists
    )
)

echo.
echo ========================================
echo Nginx Configuration Check Complete!
echo ========================================
echo.
echo Configuration file: nginx\conf\nginx.conf
echo.
echo If there are any warnings above, please fix them before starting Nginx.
echo.
echo To test Nginx configuration: nginx\nginx.exe -t
echo To start Nginx manually: nginx\nginx.exe
echo.
pause
exit /b 0
