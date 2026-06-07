@echo off
setlocal EnableDelayedExpansion

:: Make script independent of execution location
cd /d "%~dp0dont touch"

title Omega OS Installer and Launcher
color 0b

echo =========================================
echo       OMEGA OS INSTALLER AND LAUNCHER
echo =========================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not installed or not added to your system PATH.
    pause
    exit /b 1
)

:: 1. Check for Auto-Updates
echo [INFO] Initializing updater...
python updater.py

:: 2. Setup VENV and Download Requirements First
echo [INFO] Setting up virtual environment...
if not exist ".venv\Scripts\activate.bat" (
    python -m venv .venv
)
call .venv\Scripts\activate.bat

python install.py
if %ERRORLEVEL% NEQ 0 (
    pause
    exit /b 1
)

cls
echo =========================================
echo       OMEGA OS INSTALLER AND LAUNCHER
echo =========================================
echo.
echo [INFO] Required files are available.
echo.

:: 2. First Page: Language
echo =========================================
echo              SELECT LANGUAGE
echo =========================================
echo [1] English
echo [2] Hindi
echo [3] Spanish
echo [4] French
echo [5] Mandarin
echo.
:langprompt
set /p langchoice="Select your preferred language (1-5): "
if "%langchoice%"=="1" set OMEGA_LANG=en
if "%langchoice%"=="2" set OMEGA_LANG=hi
if "%langchoice%"=="3" set OMEGA_LANG=es
if "%langchoice%"=="4" set OMEGA_LANG=fr
if "%langchoice%"=="5" set OMEGA_LANG=zh
if not defined OMEGA_LANG goto langprompt

echo %OMEGA_LANG% > .lang
echo [INFO] Language saved.

:: 3. Setup Owner API Keys
echo.
echo [INFO] Loading Owner's API keys securely in memory...
set GEMINI_API_KEY=AQ.Ab8RN6KQxsvr1I_bgDMCyAP4IrdxqLYVTTu9VvtcGAlVgFadUg
set HF_API_KEY=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

:validate
echo.
echo [INFO] Checking API keys...
python omega_os\core\validate_api.py
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Owner API Keys failed validation! Please check them in Omega OS.bat.
    pause
    exit /b 1
)

:: Ensure .env exists but is empty or clear the keys so owner keys aren't saved to disk
echo # Owner API session > .env
echo [INFO] Owner Keys loaded and validated for this session.

:: Launch the application maximized
echo.
echo [INFO] All requirements met. Booting Omega OS...
echo.
start "OMEGA OS" /max cmd /c "title OMEGA OS & python main.py || (echo. & echo [CRITICAL ERROR] Omega OS crashed unexpectedly. & pause)"
exit
