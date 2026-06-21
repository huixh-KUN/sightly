@echo off
chcp 65001 >nul

cd /d "%~dp0"

echo ========================================
echo   Sightly - Standard Version
echo   Input Method: PyAutoGUI
echo ========================================
echo.

set SIGHTLY_USE_DD=0

echo Starting Sightly with PyAutoGUI...
echo.

python main.py

pause
