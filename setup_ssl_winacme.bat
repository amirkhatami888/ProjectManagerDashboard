@echo off
setlocal enabledelayedexpansion

echo ========================================
echo SSL Certificate Setup with win-acme
echo ========================================

:: Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This script must be run as Administrator
    echo Right-click and select "Run as administrator"
    pause
    exit /b 1
)

set DOMAIN=projecthelal.rcs.ir
set NGINX_DIR=%~dp0nginx
set WINACME_DIR=%~dp0win-acme

echo.
echo This script will help you set up SSL certificates using win-acme.
echo.
echo Current domain: %DOMAIN%
echo.

:: Check if win-acme is available
if not exist "%WINACME_DIR%\wacs.exe" (
    echo ERROR: win-acme not found at %WINACME_DIR%\wacs.exe
    echo Please ensure win-acme is properly installed
    pause
    exit /b 1
)

echo Options:
echo 1. Create new SSL certificate
echo 2. Renew existing certificate
echo 3. List existing certificates
echo 4. Test SSL configuration
echo 5. Interactive win-acme setup
echo 6. Exit
echo.
set /p ssl_choice="Enter your choice (1-6): "

if "%ssl_choice%"=="1" goto create_certificate
if "%ssl_choice%"=="2" goto renew_certificate
if "%ssl_choice%"=="3" goto list_certificates
if "%ssl_choice%"=="4" goto test_ssl
if "%ssl_choice%"=="5" goto interactive_setup
if "%ssl_choice%"=="6" goto exit
echo Invalid choice.
goto exit

:create_certificate
echo.
echo Creating new SSL certificate...
echo.
echo IMPORTANT: Make sure your domain %DOMAIN% points to this server's IP
echo and that port 80 is accessible from the internet.
echo.
set /p confirm="Continue with certificate creation? (y/n): "
if /i not "%confirm%"=="y" goto exit

:: Stop nginx temporarily
echo Stopping nginx...
sc stop nginx

:: Create certificate using win-acme
echo Creating SSL certificate...
cd /d "%WINACME_DIR%"
wacs.exe --target manual --host %DOMAIN% --host www.%DOMAIN% --validation http --validationmode http-01 --installation nginx --nginxserverconf "%NGINX_DIR%\conf\nginx.conf" --accepttos --emailaddress admin@%DOMAIN%

if %errorLevel% equ 0 (
    echo ✓ SSL certificate created successfully!
    
    :: Update Django settings for HTTPS
    cd /d "%~dp0"
    powershell -Command "(Get-Content '.env') -replace 'SECURE_SSL_REDIRECT=.*', 'SECURE_SSL_REDIRECT=True' | Set-Content '.env'"
    powershell -Command "(Get-Content '.env') -replace 'SESSION_COOKIE_SECURE=.*', 'SESSION_COOKIE_SECURE=True' | Set-Content '.env'"
    powershell -Command "(Get-Content '.env') -replace 'SESSION_SECURE_COOKIES=.*', 'SESSION_SECURE_COOKIES=True' | Set-Content '.env'"
    powershell -Command "(Get-Content '.env') -replace 'SESSION_CSRF_COOKIE_SECURE=.*', 'SESSION_CSRF_COOKIE_SECURE=True' | Set-Content '.env'"
    
    :: Start nginx
    echo Starting nginx...
    sc start nginx
    
    echo.
    echo ========================================
    echo SSL SETUP COMPLETED!
    echo ========================================
    echo.
    echo Your website is now available at:
    echo https://%DOMAIN%
    echo.
    echo Certificate will auto-renew via Windows Task Scheduler.
    echo.
) else (
    echo ✗ SSL certificate creation failed
    echo Starting nginx without SSL...
    sc start nginx
)
goto exit

:renew_certificate
echo.
echo Renewing SSL certificate...
cd /d "%WINACME_DIR%"
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
goto exit

:list_certificates
echo.
echo Listing existing certificates...
cd /d "%WINACME_DIR%"
wacs.exe --list
goto exit

:test_ssl
echo.
echo Testing SSL configuration...
echo.
echo Testing %DOMAIN%...
curl -I https://%DOMAIN% 2>nul
if %errorLevel% equ 0 (
    echo ✓ HTTPS is working
) else (
    echo ✗ HTTPS is not working
)

echo.
echo Testing certificate validity...
powershell "try { $cert = [System.Net.ServicePointManager]::ServerCertificateValidationCallback = {$true}; $request = [System.Net.WebRequest]::Create('https://%DOMAIN%'); $response = $request.GetResponse(); $cert = $request.ServicePoint.Certificate; $cert2 = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($cert); Write-Host 'Certificate Subject:' $cert2.Subject; Write-Host 'Certificate Issuer:' $cert2.Issuer; Write-Host 'Certificate Valid From:' $cert2.NotBefore; Write-Host 'Certificate Valid To:' $cert2.NotAfter; Write-Host 'Days Until Expiry:' ($cert2.NotAfter - (Get-Date)).Days } catch { Write-Host 'Error testing certificate:' $_.Exception.Message }"

echo.
echo SSL Labs test: https://www.ssllabs.com/ssltest/analyze.html?d=%DOMAIN%
goto exit

:interactive_setup
echo.
echo Starting interactive win-acme setup...
echo This will open the win-acme GUI for advanced configuration.
echo.
cd /d "%WINACME_DIR%"
wacs.exe
goto exit

:exit
echo.
echo ========================================
echo SSL Management Complete
echo ========================================
echo.
echo Certificate location: %WINACME_DIR%
echo.
echo Manual renewal command:
echo cd /d "%WINACME_DIR%"
echo wacs.exe --renew
echo.
echo ========================================
pause
