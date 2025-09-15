@echo off
setlocal enabledelayedexpansion

echo ========================================
echo DNS Configuration Helper
echo ========================================

:: Get public IP address
echo Detecting public IP address...
curl -s --max-time 10 https://api.ipify.org > temp_ip.txt 2>nul
if exist temp_ip.txt (
    set /p PUBLIC_IP=<temp_ip.txt
    del temp_ip.txt
    echo Public IP detected: %PUBLIC_IP%
) else (
    echo Failed to detect public IP automatically
    set /p PUBLIC_IP="Please enter your server's public IP address: "
)

:: Get domain from user
set /p DOMAIN="Enter your domain name (e.g., projecthelal.rcs.ir): "
if "%DOMAIN%"=="" set DOMAIN=projecthelal.rcs.ir

echo.
echo ========================================
echo DNS CONFIGURATION REQUIRED
echo ========================================
echo.
echo Please configure the following DNS records in your domain registrar:
echo.
echo A Record: %DOMAIN% → %PUBLIC_IP%
echo A Record: www.%DOMAIN% → %PUBLIC_IP%
echo.
echo Optional (for email):
echo MX Record: %DOMAIN% → mail.%DOMAIN% (priority 10)
echo A Record: mail.%DOMAIN% → %PUBLIC_IP%
echo.
echo ========================================
echo DNS PROPAGATION CHECK
echo ========================================
echo.
echo After configuring DNS, you can check propagation status at:
echo https://www.whatsmydns.net/#A/%DOMAIN%
echo.
echo DNS propagation usually takes 5-60 minutes.
echo.
echo ========================================
echo TESTING DNS RESOLUTION
echo ========================================
echo.

:test_dns
echo Testing DNS resolution for %DOMAIN%...
nslookup %DOMAIN% >nul 2>&1
if %errorLevel% equ 0 (
    for /f "tokens=2" %%a in ('nslookup %DOMAIN% ^| findstr "Address:"') do (
        set RESOLVED_IP=%%a
    )
    if "!RESOLVED_IP!"=="%PUBLIC_IP%" (
        echo ✓ DNS is correctly configured!
        echo %DOMAIN% resolves to %PUBLIC_IP%
        goto dns_ready
    ) else (
        echo ✗ DNS not yet propagated
        echo %DOMAIN% resolves to !RESOLVED_IP! (expected: %PUBLIC_IP%)
    )
) else (
    echo ✗ DNS not yet propagated
)

echo.
echo DNS is not ready yet. This is normal and can take up to 60 minutes.
echo.
set /p WAIT="Wait 30 seconds and test again? (y/n): "
if /i "%WAIT%"=="y" (
    echo Waiting 30 seconds...
    timeout /t 30 /nobreak >nul
    goto test_dns
)

echo.
echo You can run this script again later to test DNS propagation.
echo.
echo Manual DNS test commands:
echo nslookup %DOMAIN%
echo ping %DOMAIN%
echo.
pause
exit /b 0

:dns_ready
echo.
echo ========================================
echo DNS CONFIGURATION COMPLETE!
echo ========================================
echo.
echo Your domain %DOMAIN% is now pointing to %PUBLIC_IP%
echo.
echo You can now:
echo 1. Run the dynamic deployment script
echo 2. Test your website at http://%DOMAIN%
echo 3. Set up SSL certificates
echo.
echo ========================================
pause
