@echo off
chcp 65001 >nul
echo ========================================
echo   Sightly DD Build Script
echo   Input Method: DD Virtual Keyboard
echo ========================================
echo.

set SIGHTLY_USE_DD=1

if not exist "drivers\DD64.dll" (
    echo ERROR: DD64.dll not found
    echo Please put DD64.dll in drivers folder
    echo.
    pause
    exit /b 1
)

echo [1/3] Checking dependencies...
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

echo.
if "%1"=="--clean" (
    echo Cleaning build cache...
    if exist "build" rmdir /s /q "build"
    if exist "dist\Sightly_dd" rmdir /s /q "dist\Sightly_dd"
    echo [2/3] Building DD version (full rebuild)...
) else (
    echo [2/3] Building DD version (using cache)...
)

pyinstaller sightly.spec --noconfirm

echo.
echo [3/3] Build complete!
echo.
echo Output: dist\Sightly_dd\Sightly.exe
echo Input Method: DD Virtual Keyboard (DD Version)
echo.
echo NOTE: DD version may be flagged by antivirus software
echo.
pause