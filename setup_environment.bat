@echo off
REM Django Project Environment Setup for Windows Server 2025
REM Run this batch file as Administrator

echo Starting Django Project Environment Setup...

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH!
    echo Please install Python 3.9+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check if pip is available
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo pip is not available!
    echo Please ensure pip is installed with Python
    pause
    exit /b 1
)

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install requirements
echo Installing Python dependencies...
pip install -r requirements.txt

REM Install wfastcgi
echo Installing wfastcgi...
pip install wfastcgi

REM Enable wfastcgi
echo Enabling wfastcgi...
python -m wfastcgi.enable

REM Create logs directory
echo Creating logs directory...
if not exist "logs" mkdir logs

REM Set environment variables
echo Setting environment variables...
setx DJANGO_SETTINGS_MODULE "project_dashboard.production_settings" /M
setx PYTHONPATH "%CD%" /M

REM Run Django setup commands
echo Running Django migrations...
python manage.py makemigrations
python manage.py migrate

echo Collecting static files...
python manage.py collectstatic --noinput

echo Environment setup completed!
echo Please run the PowerShell deployment script (deploy_iis.ps1) as Administrator to complete IIS configuration.
pause
