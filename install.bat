@echo off
REM ABOUTME: Cross-platform installation script for ccthink (Windows)
REM ABOUTME: Installs to %LOCALAPPDATA% with dependency checking and PATH setup

setlocal enabledelayedexpansion

echo ===================================
echo   ccthink Installation Script
echo ===================================
echo.

REM Installation paths
set INSTALL_DIR=%LOCALAPPDATA%\Programs\ccthink
set WRAPPER_DIR=%LOCALAPPDATA%\Microsoft\WindowsApps
set WRAPPER=%WRAPPER_DIR%\ccthink.bat

REM Check Python installation
echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found
    echo Please install Python 3.10 or later from https://python.org
    pause
    exit /b 1
)

for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYTHON_VERSION=%%v
echo [OK] Found Python %PYTHON_VERSION%

REM Create installation directory
echo.
echo Creating installation directory...
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
echo [OK] Directory created: %INSTALL_DIR%

REM Copy application files
echo.
echo Installing ccthink...
xcopy /E /I /Y /Q . "%INSTALL_DIR%" >nul
echo [OK] Files copied

REM Create wrapper batch file
echo.
echo Creating ccthink launcher...
if not exist "%WRAPPER_DIR%" mkdir "%WRAPPER_DIR%"

echo @echo off > "%WRAPPER%"
echo REM ccthink launcher - preserves current directory >> "%WRAPPER%"
echo python "%%LOCALAPPDATA%%\Programs\ccthink\ccthink" %%* >> "%WRAPPER%"

echo [OK] Launcher created: %WRAPPER%

REM Check if WindowsApps is in PATH
echo.
echo Checking PATH configuration...
echo %PATH% | find /i "%WRAPPER_DIR%" >nul
if errorlevel 1 (
    echo [WARNING] %WRAPPER_DIR% is NOT in PATH
    echo.
    echo Windows 10+ usually includes this directory in PATH by default.
    echo If 'ccthink' command is not found, add this to your PATH:
    echo   %WRAPPER_DIR%
    echo.
) else (
    echo [OK] Launcher directory is in PATH
)

REM Check dependencies
echo.
echo Checking Python dependencies...
set MISSING_DEPS=

python -c "import pydantic" 2>nul || set MISSING_DEPS=!MISSING_DEPS! pydantic
python -c "import orjson" 2>nul || set MISSING_DEPS=!MISSING_DEPS! orjson
python -c "import pytest" 2>nul || set MISSING_DEPS=!MISSING_DEPS! pytest

if "!MISSING_DEPS!"=="" (
    echo [OK] All dependencies installed
) else (
    echo [WARNING] Missing dependencies:!MISSING_DEPS!
    echo.
    echo Install dependencies with:
    echo   pip install -r "%INSTALL_DIR%\requirements.txt"
    echo.
    echo Or install individually:
    echo   pip install claude-agent-sdk pydantic orjson pytest
    echo.
)

REM Create config directory
if not exist "%APPDATA%\ccthink" mkdir "%APPDATA%\ccthink"

echo.
echo ===================================
echo Installation Complete!
echo ===================================
echo.
echo Usage:
echo   1. Open Command Prompt or PowerShell
echo   2. Navigate to your project directory:
echo      cd C:\path\to\your\project
echo.
echo   3. Run ccthink:
echo      ccthink              # Start monitoring
echo      ccthink --commit     # Enable git commits
echo      ccthink --help       # Show all options
echo.
echo Each directory gets its own ccthink.conf file
echo.
echo Uninstall:
echo   Run: %INSTALL_DIR%\uninstall.bat
echo.
pause
