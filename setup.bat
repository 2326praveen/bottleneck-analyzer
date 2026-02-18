@echo off
REM OS Performance Bottleneck Analyzer - Quick Setup Script
REM This script installs all required dependencies

echo ================================
echo OS Bottleneck Analyzer - Setup
echo ================================
echo.

echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.7 or higher from https://www.python.org/
    pause
    exit /b 1
)

echo Python found!
python --version
echo.

echo Installing required packages...
echo.

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo ERROR: Installation failed
    echo Please check your internet connection and try again
    pause
    exit /b 1
)

echo.
echo ================================
echo Installation Complete!
echo ================================
echo.
echo You can now run the analyzer with:
echo   python main.py
echo.
echo Or simply double-click run.bat
echo.
pause
