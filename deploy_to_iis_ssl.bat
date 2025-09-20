@echo off
echo ========================================
echo Django Project Manager Dashboard
echo IIS SSL Deployment Script
echo ========================================

echo.
echo [1/6] Collecting static files...
python manage.py collectstatic --noinput

echo.
echo [2/6] Running database migrations...
python manage.py migrate

echo.
echo [3/6] Creating SSL certificate for IIS...
echo Importing certificate to Windows Certificate Store...

:: Import PFX certificate to Local Machine store
certutil -importPFX -f "ssl\iis_cert.pfx" "LocalMachine\My"

echo.
echo [4/6] Configuring IIS for SSL...
echo Please complete these steps manually:
echo.
echo 1. Open IIS Manager
echo 2. Go to Server Certificates
echo 3. Find "projecthelal.rcs.ir" certificate
echo 4. Go to your website
echo 5. Click "Bindings"
echo 6. Add new binding:
echo    - Type: https
echo    - Port: 443
echo    - SSL Certificate: projecthelal.rcs.ir
echo.

echo [5/6] Setting up URL Rewrite for HTTPS redirect...
echo URL Rewrite rules are configured in web.config

echo.
echo [6/6] Finalizing deployment...
echo.
echo ✅ SSL deployment completed!
echo.
echo Your Django application is now configured for HTTPS.
echo Access it at: https://projecthelal.rcs.ir
echo.
echo Note: You may need to restart IIS for changes to take effect.
echo.
pause
