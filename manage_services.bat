@echo off
setlocal enabledelayedexpansion

set SERVICE_NAME=DjangoProjectManager
set NGINX_SERVICE=nginx

echo ========================================
echo Django Website Service Manager
echo Domain: projecthelal.rcs.ir
echo ========================================

:menu
echo.
echo Select an option:
echo 1. Start all services
echo 2. Stop all services
echo 3. Restart all services
echo 4. Check service status
echo 5. View service logs
echo 6. Test website
echo 7. Exit
echo.
set /p choice="Enter your choice (1-7): "

if "%choice%"=="1" goto start_services
if "%choice%"=="2" goto stop_services
if "%choice%"=="3" goto restart_services
if "%choice%"=="4" goto check_status
if "%choice%"=="5" goto view_logs
if "%choice%"=="6" goto test_website
if "%choice%"=="7" goto exit
echo Invalid choice. Please try again.
goto menu

:start_services
echo.
echo Starting services...
sc start %NGINX_SERVICE%
if %errorLevel% equ 0 (
    echo ✓ Nginx service started
) else (
    echo ✗ Failed to start Nginx service
)

sc start %SERVICE_NAME%
if %errorLevel% equ 0 (
    echo ✓ Django service started
) else (
    echo ✗ Failed to start Django service
)
goto menu

:stop_services
echo.
echo Stopping services...
sc stop %SERVICE_NAME%
if %errorLevel% equ 0 (
    echo ✓ Django service stopped
) else (
    echo ✗ Failed to stop Django service
)

sc stop %NGINX_SERVICE%
if %errorLevel% equ 0 (
    echo ✓ Nginx service stopped
) else (
    echo ✗ Failed to stop Nginx service
)
goto menu

:restart_services
echo.
echo Restarting services...
call :stop_services
timeout /t 3 /nobreak >nul
call :start_services
goto menu

:check_status
echo.
echo Checking service status...
echo.
echo Nginx Service:
sc query %NGINX_SERVICE%
echo.
echo Django Service:
sc query %SERVICE_NAME%
echo.
echo Port Status:
netstat -an | findstr ":80 "
netstat -an | findstr ":8000 "
goto menu

:view_logs
echo.
echo Select log to view:
echo 1. Nginx Access Log
echo 2. Nginx Error Log
echo 3. Django Output Log
echo 4. Django Error Log
echo 5. Back to main menu
echo.
set /p log_choice="Enter your choice (1-5): "

if "%log_choice%"=="1" (
    if exist "nginx\logs\access.log" (
        type "nginx\logs\access.log" | more
    ) else (
        echo Nginx access log not found
    )
)
if "%log_choice%"=="2" (
    if exist "nginx\logs\error.log" (
        type "nginx\logs\error.log" | more
    ) else (
        echo Nginx error log not found
    )
)
if "%log_choice%"=="3" (
    if exist "logs\django_stdout.log" (
        type "logs\django_stdout.log" | more
    ) else (
        echo Django output log not found
    )
)
if "%log_choice%"=="4" (
    if exist "logs\django_stderr.log" (
        type "logs\django_stderr.log" | more
    ) else (
        echo Django error log not found
    )
)
if "%log_choice%"=="5" goto menu
goto view_logs

:test_website
echo.
echo Testing website connectivity...
echo.
echo Testing localhost:80...
curl -I http://localhost 2>nul | find "HTTP" >nul
if %errorLevel% equ 0 (
    echo ✓ Localhost:80 is responding
) else (
    echo ✗ Localhost:80 is not responding
)

echo.
echo Testing localhost:8000...
curl -I http://localhost:8000 2>nul | find "HTTP" >nul
if %errorLevel% equ 0 (
    echo ✓ Localhost:8000 is responding
) else (
    echo ✗ Localhost:8000 is not responding
)

echo.
echo Testing domain: projecthelal.rcs.ir...
curl -I http://projecthelal.rcs.ir 2>nul | find "HTTP" >nul
if %errorLevel% equ 0 (
    echo ✓ Domain is responding
) else (
    echo ✗ Domain is not responding (check DNS configuration)
)

echo.
echo Opening website in browser...
start http://projecthelal.rcs.ir
goto menu

:exit
echo.
echo Goodbye!
pause
exit /b 0
