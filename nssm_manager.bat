@echo off
setlocal enabledelayedexpansion

set SERVICE_NAME=DjangoProjectManager
set NGINX_SERVICE=nginx
set NSSM_DIR=%~dp0nssm

echo ========================================
echo NSSM Service Manager
echo Non-Sucking Service Manager
echo ========================================

:menu
echo.
echo Select an option:
echo 1. Open NSSM GUI
echo 2. Install nginx service
echo 3. Install Django service
echo 4. Remove nginx service
echo 5. Remove Django service
echo 6. Configure nginx service
echo 7. Configure Django service
echo 8. View service status
echo 9. Start all services
echo 10. Stop all services
echo 11. Restart all services
echo 12. View NSSM logs
echo 13. Exit
echo.
set /p choice="Enter your choice (1-13): "

if "%choice%"=="1" goto open_gui
if "%choice%"=="2" goto install_nginx
if "%choice%"=="3" goto install_django
if "%choice%"=="4" goto remove_nginx
if "%choice%"=="5" goto remove_django
if "%choice%"=="6" goto configure_nginx
if "%choice%"=="7" goto configure_django
if "%choice%"=="8" goto view_status
if "%choice%"=="9" goto start_services
if "%choice%"=="10" goto stop_services
if "%choice%"=="11" goto restart_services
if "%choice%"=="12" goto view_logs
if "%choice%"=="13" goto exit
echo Invalid choice. Please try again.
goto menu

:open_gui
echo.
echo Opening NSSM GUI...
"%NSSM_DIR%\win64\nssm.exe" gui
goto menu

:install_nginx
echo.
echo Installing nginx service with NSSM...
set NGINX_DIR=%~dp0nginx
set PYTHON_PATH=C:\Python39\python.exe

:: Stop existing service
sc stop %NGINX_SERVICE% >nul 2>&1
sc delete %NGINX_SERVICE% >nul 2>&1

:: Install service
"%NSSM_DIR%\win64\nssm.exe" install %NGINX_SERVICE% "%NGINX_DIR%\nginx.exe"
if %errorLevel% equ 0 (
    echo ✓ nginx service installed successfully
) else (
    echo ✗ Failed to install nginx service
)
goto menu

:install_django
echo.
echo Installing Django service with NSSM...
set PROJECT_DIR=%~dp0
set PYTHON_PATH=C:\Python39\python.exe

:: Stop existing service
sc stop %SERVICE_NAME% >nul 2>&1
sc delete %SERVICE_NAME% >nul 2>&1

:: Install service
"%NSSM_DIR%\win64\nssm.exe" install %SERVICE_NAME% "%PYTHON_PATH%" "runserver 127.0.0.1:8000"
if %errorLevel% equ 0 (
    echo ✓ Django service installed successfully
) else (
    echo ✗ Failed to install Django service
)
goto menu

:remove_nginx
echo.
echo Removing nginx service...
sc stop %NGINX_SERVICE% >nul 2>&1
"%NSSM_DIR%\win64\nssm.exe" remove %NGINX_SERVICE% confirm
if %errorLevel% equ 0 (
    echo ✓ nginx service removed successfully
) else (
    echo ✗ Failed to remove nginx service
)
goto menu

:remove_django
echo.
echo Removing Django service...
sc stop %SERVICE_NAME% >nul 2>&1
"%NSSM_DIR%\win64\nssm.exe" remove %SERVICE_NAME% confirm
if %errorLevel% equ 0 (
    echo ✓ Django service removed successfully
) else (
    echo ✗ Failed to remove Django service
)
goto menu

:configure_nginx
echo.
echo Configuring nginx service...
set NGINX_DIR=%~dp0nginx

:: Configure nginx service
"%NSSM_DIR%\win64\nssm.exe" set %NGINX_SERVICE% AppDirectory "%NGINX_DIR%"
"%NSSM_DIR%\win64\nssm.exe" set %NGINX_SERVICE% AppStdout "%NGINX_DIR%\logs\nginx_stdout.log"
"%NSSM_DIR%\win64\nssm.exe" set %NGINX_SERVICE% AppStderr "%NGINX_DIR%\logs\nginx_stderr.log"
"%NSSM_DIR%\win64\nssm.exe" set %NGINX_SERVICE% Start SERVICE_AUTO_START
"%NSSM_DIR%\win64\nssm.exe" set %NGINX_SERVICE% DisplayName "Nginx Web Server"
"%NSSM_DIR%\win64\nssm.exe" set %NGINX_SERVICE% Description "Nginx web server for Django application"
"%NSSM_DIR%\win64\nssm.exe" set %NGINX_SERVICE% AppExit Default Restart
"%NSSM_DIR%\win64\nssm.exe" set %NGINX_SERVICE% AppRestartDelay 5000
"%NSSM_DIR%\win64\nssm.exe" set %NGINX_SERVICE% AppThrottle 1500
"%NSSM_DIR%\win64\nssm.exe" set %NGINX_SERVICE% AppStopMethodSkip 0
"%NSSM_DIR%\win64\nssm.exe" set %NGINX_SERVICE% AppStopMethodConsole 15000
"%NSSM_DIR%\win64\nssm.exe" set %NGINX_SERVICE% AppStopMethodWindow 15000
"%NSSM_DIR%\win64\nssm.exe" set %NGINX_SERVICE% AppStopMethodThreads 15000

echo ✓ nginx service configured successfully
goto menu

:configure_django
echo.
echo Configuring Django service...
set PROJECT_DIR=%~dp0

:: Configure Django service
"%NSSM_DIR%\win64\nssm.exe" set %SERVICE_NAME% AppDirectory "%PROJECT_DIR%"
"%NSSM_DIR%\win64\nssm.exe" set %SERVICE_NAME% AppStdout "%PROJECT_DIR%\logs\django_stdout.log"
"%NSSM_DIR%\win64\nssm.exe" set %SERVICE_NAME% AppStderr "%PROJECT_DIR%\logs\django_stderr.log"
"%NSSM_DIR%\win64\nssm.exe" set %SERVICE_NAME% Start SERVICE_AUTO_START
"%NSSM_DIR%\win64\nssm.exe" set %SERVICE_NAME% DisplayName "Django Project Manager"
"%NSSM_DIR%\win64\nssm.exe" set %SERVICE_NAME% Description "Django Project Manager Dashboard Application"
"%NSSM_DIR%\win64\nssm.exe" set %SERVICE_NAME% AppExit Default Restart
"%NSSM_DIR%\win64\nssm.exe" set %SERVICE_NAME% AppRestartDelay 10000
"%NSSM_DIR%\win64\nssm.exe" set %SERVICE_NAME% AppThrottle 1500
"%NSSM_DIR%\win64\nssm.exe" set %SERVICE_NAME% AppStopMethodSkip 0
"%NSSM_DIR%\win64\nssm.exe" set %SERVICE_NAME% AppStopMethodConsole 30000
"%NSSM_DIR%\win64\nssm.exe" set %SERVICE_NAME% AppStopMethodWindow 30000
"%NSSM_DIR%\win64\nssm.exe" set %SERVICE_NAME% AppStopMethodThreads 30000
"%NSSM_DIR%\win64\nssm.exe" set %SERVICE_NAME% AppEnvironmentExtra "DJANGO_SETTINGS_MODULE=project_dashboard.settings" "PYTHONPATH=%PROJECT_DIR%"

echo ✓ Django service configured successfully
goto menu

:view_status
echo.
echo Service Status:
echo ========================================
echo.
echo Nginx Service:
sc query %NGINX_SERVICE%
echo.
echo Django Service:
sc query %SERVICE_NAME%
echo.
echo NSSM Service Information:
echo.
echo Nginx NSSM Config:
"%NSSM_DIR%\win64\nssm.exe" get %NGINX_SERVICE% AppDirectory
"%NSSM_DIR%\win64\nssm.exe" get %NGINX_SERVICE% AppStdout
"%NSSM_DIR%\win64\nssm.exe" get %NGINX_SERVICE% AppStderr
echo.
echo Django NSSM Config:
"%NSSM_DIR%\win64\nssm.exe" get %SERVICE_NAME% AppDirectory
"%NSSM_DIR%\win64\nssm.exe" get %SERVICE_NAME% AppStdout
"%NSSM_DIR%\win64\nssm.exe" get %SERVICE_NAME% AppStderr
goto menu

:start_services
echo.
echo Starting services...
sc start %NGINX_SERVICE%
if %errorLevel% equ 0 (
    echo ✓ nginx service started
) else (
    echo ✗ Failed to start nginx service
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
    echo ✓ nginx service stopped
) else (
    echo ✗ Failed to stop nginx service
)
goto menu

:restart_services
echo.
echo Restarting services...
call :stop_services
timeout /t 3 /nobreak >nul
call :start_services
goto menu

:view_logs
echo.
echo NSSM Logs and Service Information:
echo ========================================
echo.
echo Recent Windows Event Log entries for NSSM:
wevtutil qe System /c:10 /rd:true /f:text | findstr /i "nssm"
echo.
echo Service Log Files:
echo - Nginx stdout: nginx\logs\nginx_stdout.log
echo - Nginx stderr: nginx\logs\nginx_stderr.log
echo - Django stdout: logs\django_stdout.log
echo - Django stderr: logs\django_stderr.log
echo.
echo To view real-time logs, use the advanced service manager.
goto menu

:exit
echo.
echo Goodbye!
pause
exit /b 0
