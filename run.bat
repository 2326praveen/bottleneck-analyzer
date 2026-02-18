@echo off
REM OS Performance Bottleneck Analyzer - Quick Run Script

echo Starting OS Performance Bottleneck Analyzer...
echo.

python main.py

if errorlevel 1 (
    echo.
    echo ERROR: Failed to start the application
    echo.
    echo Make sure you have run setup.bat first to install dependencies
    echo.
    pause
)
