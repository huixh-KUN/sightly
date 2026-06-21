@echo off
chcp 65001 >nul
echo ========================================
echo   Sightly Windows Build Script
echo ========================================
echo.

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
    if exist "dist\Sightly" rmdir /s /q "dist\Sightly"
    echo [2/3] Building Windows version (full rebuild)...
) else (
    echo [2/3] Building Windows version (using cache)...
)

pyinstaller sightly.spec --noconfirm

echo.
echo [3/3] Build complete!
echo.
echo Output: dist\Sightly\
echo.
pause