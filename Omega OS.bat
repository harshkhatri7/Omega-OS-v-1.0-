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

:validate
echo.
echo [INFO] Checking API keys...
python omega_os\core\validate_api.py
if %ERRORLEVEL% EQU 0 goto boot

:apiwizard
echo.
echo =========================================
echo             API SETUP WIZARD
echo =========================================
echo Omega OS requires API keys for AI capabilities.
echo It seems your keys are missing or invalid.
echo.
echo We will open the API creation pages for you in...
timeout /t 5
start https://aistudio.google.com/app/apikey
start https://huggingface.co/settings/tokens
echo.
set /p user_gemini="Paste your Gemini API Key: "
set /p user_hf="Paste your Hugging Face API Key: "
echo GEMINI_API_KEY="%user_gemini%" > .env
echo HF_API_KEY="%user_hf%" >> .env
echo [INFO] Keys saved.
goto validate

:boot
:: Launch the application maximized
echo.
echo [INFO] All requirements met. Booting Omega OS...
echo.
start "OMEGA OS" /max cmd /c "title OMEGA OS & python main.py || (echo. & echo [CRITICAL ERROR] Omega OS crashed unexpectedly. & pause)"
exit
