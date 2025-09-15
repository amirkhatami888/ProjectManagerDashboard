@echo off
setlocal enabledelayedexpansion

echo ========================================
echo NSSM Troubleshooting Tool
echo ========================================

set NSSM_DIR=%~dp0nssm

echo.
echo Checking NSSM installation...
echo.

:: Check if NSSM directory exists
if not exist "%NSSM_DIR%" (
    echo ERROR: NSSM directory not found at: %NSSM_DIR%
    echo Please ensure NSSM is extracted to the nssm folder
    pause
    exit /b 1
) else (
    echo ✓ NSSM directory exists: %NSSM_DIR%
)

:: Check if nssm.exe exists
if not exist "%NSSM_DIR%\win64\nssm.exe" (
    echo ERROR: nssm.exe not found at: %NSSM_DIR%\win64\nssm.exe
    echo.
    echo Available files in nssm directory:
    dir "%NSSM_DIR%" /b
    echo.
    echo Available files in win64 directory:
    if exist "%NSSM_DIR%\win64" (
        dir "%NSSM_DIR%\win64" /b
    ) else (
        echo win64 directory does not exist
    )
    pause
    exit /b 1
) else (
    echo ✓ nssm.exe found at: %NSSM_DIR%\win64\nssm.exe
)

:: Check file size
for %%A in ("%NSSM_DIR%\win64\nssm.exe") do set FILE_SIZE=%%~zA
echo ✓ File size: %FILE_SIZE% bytes

:: Check if file is executable
echo.
echo Testing NSSM execution...
echo.

:: Try to run NSSM version command
echo Running: "%NSSM_DIR%\win64\nssm.exe" version
"%NSSM_DIR%\win64\nssm.exe" version
set NSSM_EXIT_CODE=%errorLevel%

echo.
echo NSSM exit code: %NSSM_EXIT_CODE%

if %NSSM_EXIT_CODE% equ 0 (
    echo ✓ NSSM is working correctly!
) else (
    echo ✗ NSSM execution failed
    echo.
    echo Possible causes:
    echo 1. File is corrupted
    echo 2. Antivirus is blocking the file
    echo 3. Missing dependencies (Visual C++ Redistributable)
    echo 4. File permissions issue
    echo.
    
    :: Check file permissions
    echo Checking file permissions...
    icacls "%NSSM_DIR%\win64\nssm.exe" | find "Everyone"
    if %errorLevel% equ 0 (
        echo ✓ File permissions look OK
    ) else (
        echo ⚠ File permissions may be restricted
    )
    
    :: Check if antivirus might be blocking
    echo.
    echo Checking if antivirus might be blocking...
    echo Try temporarily disabling antivirus and running again.
    echo.
    
    :: Try to copy to temp directory and run
    echo Testing by copying to temp directory...
    copy "%NSSM_DIR%\win64\nssm.exe" "%TEMP%\nssm_test.exe" >nul 2>&1
    if %errorLevel% equ 0 (
        echo ✓ File copied successfully
        echo Testing from temp directory...
        "%TEMP%\nssm_test.exe" version
        if %errorLevel% equ 0 (
            echo ✓ NSSM works from temp directory
            echo This suggests the original location might be blocked
        ) else (
            echo ✗ NSSM still fails from temp directory
            echo This suggests the file itself is corrupted
        )
        del "%TEMP%\nssm_test.exe" >nul 2>&1
    ) else (
        echo ✗ Could not copy file to temp directory
    )
)

:: Check system requirements
echo.
echo Checking system requirements...
echo.

:: Check Windows version
echo Windows version:
ver

:: Check if running as administrator
net session >nul 2>&1
if %errorLevel% equ 0 (
    echo ✓ Running as Administrator
) else (
    echo ✗ NOT running as Administrator
    echo NSSM requires Administrator privileges
)

:: Check Visual C++ Redistributable
echo.
echo Checking for Visual C++ Redistributable...
reg query "HKLM\SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64" >nul 2>&1
if %errorLevel% equ 0 (
    echo ✓ Visual C++ 2015-2019 Redistributable (x64) found
) else (
    echo ⚠ Visual C++ 2015-2019 Redistributable (x64) not found
    echo This might be required for NSSM to work
)

:: Check alternative NSSM locations
echo.
echo Checking for NSSM in system directories...
if exist "C:\Windows\System32\nssm.exe" (
    echo ✓ NSSM found in System32
    echo Testing system NSSM...
    "C:\Windows\System32\nssm.exe" version
    if %errorLevel% equ 0 (
        echo ✓ System NSSM is working
    ) else (
        echo ✗ System NSSM is not working
    )
) else (
    echo - NSSM not found in System32
)

:: Provide solutions
echo.
echo ========================================
echo TROUBLESHOOTING SOLUTIONS
echo ========================================
echo.

if %NSSM_EXIT_CODE% neq 0 (
    echo If NSSM is not working, try these solutions:
    echo.
    echo 1. Download NSSM again:
    echo    - Go to https://nssm.cc/download
    echo    - Download the latest version
    echo    - Extract to the nssm folder
    echo.
    echo 2. Install Visual C++ Redistributable:
    echo    - Download from Microsoft website
    echo    - Install both x86 and x64 versions
    echo.
    echo 3. Temporarily disable antivirus:
    echo    - Add nssm.exe to antivirus exclusions
    echo    - Or temporarily disable real-time protection
    echo.
    echo 4. Run as Administrator:
    echo    - Right-click Command Prompt
    echo    - Select "Run as administrator"
    echo.
    echo 5. Use alternative service installation:
    echo    - The deployment script will fall back to SC command
    echo    - This provides basic service functionality
) else (
    echo NSSM is working correctly!
    echo You can proceed with the deployment.
)

echo.
echo ========================================
pause
