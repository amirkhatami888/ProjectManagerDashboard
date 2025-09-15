@echo off
setlocal enabledelayedexpansion

set SERVICE_NAME=DjangoProjectManager
set NGINX_SERVICE=nginx
set DOMAIN=projecthelal.rcs.ir

echo ========================================
echo Advanced Django Website Service Manager
echo Domain: %DOMAIN%
echo ========================================

:menu
echo.
echo Select an option:
echo 1. Start all services
echo 2. Stop all services
echo 3. Restart all services
echo 4. Check service status
echo 5. View service logs
echo 6. Test website connectivity
echo 7. Monitor real-time logs
echo 8. Database management
echo 9. SSL certificate management
echo 10. Backup website
echo 11. Restore website
echo 12. Update website
echo 13. Performance monitoring
echo 14. Security check
echo 15. Exit
echo.
set /p choice="Enter your choice (1-15): "

if "%choice%"=="1" goto start_services
if "%choice%"=="2" goto stop_services
if "%choice%"=="3" goto restart_services
if "%choice%"=="4" goto check_status
if "%choice%"=="5" goto view_logs
if "%choice%"=="6" goto test_website
if "%choice%"=="7" goto monitor_logs
if "%choice%"=="8" goto database_management
if "%choice%"=="9" goto ssl_management
if "%choice%"=="10" goto backup_website
if "%choice%"=="11" goto restore_website
if "%choice%"=="12" goto update_website
if "%choice%"=="13" goto performance_monitoring
if "%choice%"=="14" goto security_check
if "%choice%"=="15" goto exit
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
netstat -an | findstr ":443 "
netstat -an | findstr ":8000 "
echo.
echo Process Status:
tasklist | findstr "nginx.exe"
tasklist | findstr "python.exe"
goto menu

:view_logs
echo.
echo Select log to view:
echo 1. Nginx Access Log
echo 2. Nginx Error Log
echo 3. Django Output Log
echo 4. Django Error Log
echo 5. System Event Log
echo 6. Back to main menu
echo.
set /p log_choice="Enter your choice (1-6): "

if "%log_choice%"=="1" (
    if exist "nginx\logs\access.log" (
        echo Last 50 lines of Nginx Access Log:
        echo ========================================
        powershell "Get-Content 'nginx\logs\access.log' | Select-Object -Last 50"
    ) else (
        echo Nginx access log not found
    )
)
if "%log_choice%"=="2" (
    if exist "nginx\logs\error.log" (
        echo Last 50 lines of Nginx Error Log:
        echo ========================================
        powershell "Get-Content 'nginx\logs\error.log' | Select-Object -Last 50"
    ) else (
        echo Nginx error log not found
    )
)
if "%log_choice%"=="3" (
    if exist "logs\django_stdout.log" (
        echo Last 50 lines of Django Output Log:
        echo ========================================
        powershell "Get-Content 'logs\django_stdout.log' | Select-Object -Last 50"
    ) else (
        echo Django output log not found
    )
)
if "%log_choice%"=="4" (
    if exist "logs\django_stderr.log" (
        echo Last 50 lines of Django Error Log:
        echo ========================================
        powershell "Get-Content 'logs\django_stderr.log' | Select-Object -Last 50"
    ) else (
        echo Django error log not found
    )
)
if "%log_choice%"=="5" (
    echo Recent system events related to services:
    echo ========================================
    wevtutil qe System /c:20 /rd:true /f:text | findstr /i "nginx django"
)
if "%log_choice%"=="6" goto menu
pause
goto view_logs

:monitor_logs
echo.
echo Real-time log monitoring (Press Ctrl+C to stop)
echo ========================================
echo.
echo Select log to monitor:
echo 1. Nginx Access Log
echo 2. Nginx Error Log
echo 3. Django Output Log
echo 4. Django Error Log
echo 5. Back to main menu
echo.
set /p monitor_choice="Enter your choice (1-5): "

if "%monitor_choice%"=="1" (
    if exist "nginx\logs\access.log" (
        echo Monitoring Nginx Access Log...
        powershell "Get-Content 'nginx\logs\access.log' -Wait -Tail 10"
    ) else (
        echo Nginx access log not found
    )
)
if "%monitor_choice%"=="2" (
    if exist "nginx\logs\error.log" (
        echo Monitoring Nginx Error Log...
        powershell "Get-Content 'nginx\logs\error.log' -Wait -Tail 10"
    ) else (
        echo Nginx error log not found
    )
)
if "%monitor_choice%"=="3" (
    if exist "logs\django_stdout.log" (
        echo Monitoring Django Output Log...
        powershell "Get-Content 'logs\django_stdout.log' -Wait -Tail 10"
    ) else (
        echo Django output log not found
    )
)
if "%monitor_choice%"=="4" (
    if exist "logs\django_stderr.log" (
        echo Monitoring Django Error Log...
        powershell "Get-Content 'logs\django_stderr.log' -Wait -Tail 10"
    ) else (
        echo Django error log not found
    )
)
if "%monitor_choice%"=="5" goto menu
goto monitor_logs

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
echo Testing domain: %DOMAIN%...
curl -I http://%DOMAIN% 2>nul | find "HTTP" >nul
if %errorLevel% equ 0 (
    echo ✓ Domain HTTP is responding
) else (
    echo ✗ Domain HTTP is not responding
)

echo.
echo Testing HTTPS: %DOMAIN%...
curl -I https://%DOMAIN% 2>nul | find "HTTP" >nul
if %errorLevel% equ 0 (
    echo ✓ Domain HTTPS is responding
) else (
    echo ✗ Domain HTTPS is not responding (SSL may not be configured)
)

echo.
echo Response time test:
powershell "Measure-Command { Invoke-WebRequest -Uri 'http://%DOMAIN%' -UseBasicParsing } | Select-Object TotalMilliseconds"

echo.
echo Opening website in browser...
start http://%DOMAIN%
goto menu

:database_management
echo.
echo Database Management:
echo 1. Create database backup
echo 2. Restore database from backup
echo 3. Run database migrations
echo 4. Check database status
echo 5. Optimize database
echo 6. Back to main menu
echo.
set /p db_choice="Enter your choice (1-6): "

if "%db_choice%"=="1" (
    echo Creating database backup...
    set BACKUP_FILE=backup_%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%.sql
    set BACKUP_FILE=!BACKUP_FILE: =0!
    mysqldump -u django_user -pdjango_password_2024 project_manager_db > "backups\!BACKUP_FILE!"
    if %errorLevel% equ 0 (
        echo ✓ Database backup created: backups\!BACKUP_FILE!
    ) else (
        echo ✗ Database backup failed
    )
)
if "%db_choice%"=="2" (
    echo Available backups:
    dir /b backups\*.sql 2>nul
    if %errorLevel% neq 0 (
        echo No backups found
        goto database_management
    )
    set /p backup_file="Enter backup filename: "
    if exist "backups\%backup_file%" (
        echo Restoring database from %backup_file%...
        mysql -u django_user -pdjango_password_2024 project_manager_db < "backups\%backup_file%"
        if %errorLevel% equ 0 (
            echo ✓ Database restored successfully
        ) else (
            echo ✗ Database restore failed
        )
    ) else (
        echo Backup file not found
    )
)
if "%db_choice%"=="3" (
    echo Running database migrations...
    C:\Python39\python.exe manage.py migrate
    if %errorLevel% equ 0 (
        echo ✓ Migrations completed successfully
    ) else (
        echo ✗ Migration failed
    )
)
if "%db_choice%"=="4" (
    echo Database status:
    mysql -u django_user -pdjango_password_2024 -e "SHOW DATABASES;"
    mysql -u django_user -pdjango_password_2024 -e "USE project_manager_db; SHOW TABLES;"
)
if "%db_choice%"=="5" (
    echo Optimizing database...
    mysql -u django_user -pdjango_password_2024 -e "USE project_manager_db; OPTIMIZE TABLE *;"
    if %errorLevel% equ 0 (
        echo ✓ Database optimization completed
    ) else (
        echo ✗ Database optimization failed
    )
)
if "%db_choice%"=="6" goto menu
pause
goto database_management

:ssl_management
echo.
echo SSL Certificate Management:
echo 1. Check certificate status
echo 2. Renew certificate
echo 3. Test SSL configuration
echo 4. View certificate details
echo 5. Back to main menu
echo.
set /p ssl_choice="Enter your choice (1-5): "

if "%ssl_choice%"=="1" (
    echo Checking SSL certificate status...
    if exist "win-acme\wacs.exe" (
        cd /d "win-acme"
        wacs.exe --list
        cd /d "%~dp0"
    ) else (
        echo win-acme not found
    )
)
if "%ssl_choice%"=="2" (
    echo Renewing SSL certificate...
    if exist "win-acme\wacs.exe" (
        cd /d "win-acme"
        wacs.exe --renew --baseuri https://acme-v02.api.letsencrypt.org/
        if %errorLevel% equ 0 (
            echo ✓ Certificate renewed successfully
            echo Restarting nginx...
            sc stop nginx
            timeout /t 2 /nobreak >nul
            sc start nginx
        ) else (
            echo ✗ Certificate renewal failed
        )
        cd /d "%~dp0"
    ) else (
        echo win-acme not found
    )
)
if "%ssl_choice%"=="3" (
    echo Testing SSL configuration...
    echo Testing %DOMAIN%...
    curl -I https://%DOMAIN% 2>nul
    echo.
    echo SSL Labs test: https://www.ssllabs.com/ssltest/analyze.html?d=%DOMAIN%
)
if "%ssl_choice%"=="4" (
    echo Certificate details:
    if exist "win-acme\wacs.exe" (
        cd /d "win-acme"
        wacs.exe --list
        cd /d "%~dp0"
    ) else (
        echo win-acme not found
    )
)
if "%ssl_choice%"=="5" goto menu
pause
goto ssl_management

:backup_website
echo.
echo Creating website backup...
set BACKUP_DIR=backups\backup_%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set BACKUP_DIR=!BACKUP_DIR: =0!

if not exist "backups" mkdir backups
mkdir "%BACKUP_DIR%"

echo Backing up database...
mysqldump -u django_user -pdjango_password_2024 project_manager_db > "%BACKUP_DIR%\database.sql"

echo Backing up media files...
xcopy media "%BACKUP_DIR%\media\" /E /I /Q

echo Backing up static files...
xcopy staticfiles "%BACKUP_DIR%\staticfiles\" /E /I /Q

echo Backing up configuration...
copy .env "%BACKUP_DIR%\"
copy nginx\conf\nginx.conf "%BACKUP_DIR%\"

echo Creating backup archive...
powershell "Compress-Archive -Path '%BACKUP_DIR%' -DestinationPath '%BACKUP_DIR%.zip'"
rmdir /s /q "%BACKUP_DIR%"

echo ✓ Website backup created: %BACKUP_DIR%.zip
goto menu

:restore_website
echo.
echo Restore website from backup:
echo Available backups:
dir /b backups\*.zip 2>nul
if %errorLevel% neq 0 (
    echo No backups found
    goto menu
)
set /p restore_file="Enter backup filename: "
if exist "backups\%restore_file%" (
    echo Restoring website from %restore_file%...
    powershell "Expand-Archive -Path 'backups\%restore_file%' -DestinationPath 'temp_restore' -Force"
    echo Restoring database...
    mysql -u django_user -pdjango_password_2024 project_manager_db < "temp_restore\*\database.sql"
    echo Restoring media files...
    xcopy "temp_restore\*\media" media\ /E /I /Q /Y
    echo Restoring static files...
    xcopy "temp_restore\*\staticfiles" staticfiles\ /E /I /Q /Y
    echo Restoring configuration...
    copy "temp_restore\*\.env" .env /Y
    copy "temp_restore\*\nginx.conf" nginx\conf\nginx.conf /Y
    rmdir /s /q temp_restore
    echo ✓ Website restored successfully
    echo Please restart services to apply changes
) else (
    echo Backup file not found
)
goto menu

:update_website
echo.
echo Updating website...
echo 1. Update Python packages
echo 2. Update Django application
echo 3. Update nginx configuration
echo 4. Full system update
echo 5. Back to main menu
echo.
set /p update_choice="Enter your choice (1-5): "

if "%update_choice%"=="1" (
    echo Updating Python packages...
    C:\Python39\python.exe -m pip install --upgrade -r requirements.txt
    echo ✓ Python packages updated
)
if "%update_choice%"=="2" (
    echo Updating Django application...
    C:\Python39\python.exe manage.py collectstatic --noinput
    C:\Python39\python.exe manage.py migrate
    echo ✓ Django application updated
)
if "%update_choice%"=="3" (
    echo Updating nginx configuration...
    sc stop nginx
    timeout /t 2 /nobreak >nul
    sc start nginx
    echo ✓ Nginx configuration updated
)
if "%update_choice%"=="4" (
    echo Performing full system update...
    C:\Python39\python.exe -m pip install --upgrade -r requirements.txt
    C:\Python39\python.exe manage.py collectstatic --noinput
    C:\Python39\python.exe manage.py migrate
    sc stop DjangoProjectManager
    sc stop nginx
    timeout /t 3 /nobreak >nul
    sc start nginx
    sc start DjangoProjectManager
    echo ✓ Full system update completed
)
if "%update_choice%"=="5" goto menu
pause
goto update_website

:performance_monitoring
echo.
echo Performance Monitoring:
echo 1. System resource usage
echo 2. Website response time
echo 3. Database performance
echo 4. Nginx statistics
echo 5. Back to main menu
echo.
set /p perf_choice="Enter your choice (1-5): "

if "%perf_choice%"=="1" (
    echo System Resource Usage:
    echo ========================================
    echo CPU Usage:
    wmic cpu get loadpercentage /value
    echo.
    echo Memory Usage:
    wmic OS get TotalVisibleMemorySize,FreePhysicalMemory /value
    echo.
    echo Disk Usage:
    wmic logicaldisk get size,freespace,caption
)
if "%perf_choice%"=="2" (
    echo Website Response Time Test:
    echo ========================================
    for /l %%i in (1,1,5) do (
        echo Test %%i:
        powershell "Measure-Command { Invoke-WebRequest -Uri 'http://%DOMAIN%' -UseBasicParsing } | Select-Object TotalMilliseconds"
    )
)
if "%perf_choice%"=="3" (
    echo Database Performance:
    echo ========================================
    mysql -u django_user -pdjango_password_2024 -e "SHOW PROCESSLIST;"
    mysql -u django_user -pdjango_password_2024 -e "SHOW STATUS LIKE 'Connections';"
    mysql -u django_user -pdjango_password_2024 -e "SHOW STATUS LIKE 'Uptime';"
)
if "%perf_choice%"=="4" (
    echo Nginx Statistics:
    echo ========================================
    echo Active connections:
    netstat -an | findstr ":80 " | find "ESTABLISHED"
    echo.
    echo Nginx process info:
    tasklist | findstr "nginx.exe"
)
if "%perf_choice%"=="5" goto menu
pause
goto performance_monitoring

:security_check
echo.
echo Security Check:
echo 1. Check open ports
echo 2. Check firewall status
echo 3. Check SSL certificate
echo 4. Check for security updates
echo 5. Back to main menu
echo.
set /p sec_choice="Enter your choice (1-5): "

if "%sec_choice%"=="1" (
    echo Open Ports:
    echo ========================================
    netstat -an | findstr "LISTENING"
)
if "%sec_choice%"=="2" (
    echo Firewall Status:
    echo ========================================
    netsh advfirewall show allprofiles
)
if "%sec_choice%"=="3" (
    echo SSL Certificate Check:
    echo ========================================
    echo Testing SSL for %DOMAIN%...
    curl -I https://%DOMAIN% 2>nul
    echo.
    echo Certificate expiration:
    certbot certificates
)
if "%sec_choice%"=="4" (
    echo Checking for security updates...
    echo Python packages:
    C:\Python39\python.exe -m pip list --outdated
    echo.
    echo Windows updates:
    powershell "Get-WindowsUpdate"
)
if "%sec_choice%"=="5" goto menu
pause
goto security_check

:exit
echo.
echo Goodbye!
pause
exit /b 0
