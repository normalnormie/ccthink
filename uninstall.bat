@echo off
REM ABOUTME: Uninstallation script for ccthink (Windows)
REM ABOUTME: Clears installation while preserving project-specific configs

setlocal

echo ===================================
echo   ccthink Uninstallation Script
echo ===================================
echo.

set INSTALL_DIR=%LOCALAPPDATA%\Programs\ccthink
set WRAPPER=%LOCALAPPDATA%\Microsoft\WindowsApps\ccthink.bat

echo This will remove:
echo   - %INSTALL_DIR%
echo   - %WRAPPER%
echo.
echo This will be preserved:
echo   - Project-specific ccthink.conf files
echo   - %APPDATA%\ccthink directory
echo.

set /p CONFIRM=Continue? (y/N):
if /i not "%CONFIRM%"=="y" (
    echo Uninstallation cancelled
    pause
    exit /b 0
)

echo.
echo Uninstalling ccthink...

REM Remove wrapper
if exist "%WRAPPER%" (
    del /F /Q "%WRAPPER%"
    echo [OK] Launcher removed: %WRAPPER% & REM noqm
) else (
    echo [WARNING] Launcher not found: %WRAPPER%
)

REM Remove installation directory
if exist "%INSTALL_DIR%" (
    rmdir /S /Q "%INSTALL_DIR%"
    echo [OK] Installation removed: %INSTALL_DIR% & REM noqm
) else (
    echo [WARNING] Installation directory not found: %INSTALL_DIR%
)

echo.
echo ===================================
echo Uninstallation Complete!
echo ===================================
echo.
echo Note: Project-specific config files preserved
echo To remove all ccthink data:
echo   rmdir /S "%APPDATA%\ccthink"
echo   (Then manually delete ccthink.conf files from your projects)
echo.
pause
