@echo off
setlocal EnableDelayedExpansion
title OMEGA OS - Security Access IO
color 0c

:: Move to script directory
cd /d "%~dp0"

:menu
cls
echo =========================================
echo       OMEGA OS SECURITY - ACCESS IO
echo =========================================
echo.
echo [1] Free Files (Unlock all core files)
echo [2] Lock Files (Protect core files from deletion/edits)
echo [3] Exit
echo.
set /p choice="Select an option (1-3): "

if "%choice%"=="1" goto unlock
if "%choice%"=="2" goto lock
if "%choice%"=="3" exit
goto menu

:lock
echo.
echo [INFO] Locking important core files...
icacls "omega_os\*.py" /deny *S-1-1-0:(W,D) /T >nul 2>&1
icacls "main.py" /deny *S-1-1-0:(W,D) >nul 2>&1
icacls "install.py" /deny *S-1-1-0:(W,D) >nul 2>&1
icacls "requirements.txt" /deny *S-1-1-0:(W,D) >nul 2>&1
icacls "list_models.py" /deny *S-1-1-0:(W,D) >nul 2>&1
echo [SUCCESS] Files are now LOCKED. They cannot be edited or deleted.
pause
goto menu

:unlock
echo.
echo =========================================
echo             SECURITY CAPTCHA
echo =========================================
set /a n1=%random% %% 10 + 1
set /a n2=%random% %% 10 + 1
set /a ans=n1+n2

set /p userans="To unlock, what is !n1! + !n2!? "

if "!userans!"=="!ans!" (
    echo.
    echo [INFO] Captcha passed. Unlocking files...
    icacls "omega_os\*.py" /remove:d *S-1-1-0 /T >nul 2>&1
    icacls "main.py" /remove:d *S-1-1-0 >nul 2>&1
    icacls "install.py" /remove:d *S-1-1-0 >nul 2>&1
    icacls "requirements.txt" /remove:d *S-1-1-0 >nul 2>&1
    icacls "list_models.py" /remove:d *S-1-1-0 >nul 2>&1
    echo [SUCCESS] Files are now FREE.
) else (
    echo.
    echo [ERROR] Captcha failed. Files remain locked.
)
pause
goto menu
