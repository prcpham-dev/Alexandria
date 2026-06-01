@echo off
cd /d "%~dp0"
title Alexandria

echo.
echo  Alexandria - Transcript Cleaner
echo  ================================
echo.

:: Check Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo  ERROR: Python is not installed.
    echo.
    echo  Please install Python 3 from:
    echo    https://www.python.org/downloads/
    echo.
    echo  Make sure to check "Add Python to PATH" during install.
    echo.
    pause
    exit /b 1
)

:: First-time setup: create venv and install dependencies
if not exist "venv\Scripts\python.exe" (
    echo  First-time setup - this only happens once...
    echo.
    python -m venv venv
    if errorlevel 1 (
        echo  ERROR: Could not create virtual environment.
        pause
        exit /b 1
    )
    venv\Scripts\pip install python-docx --quiet
    if errorlevel 1 (
        echo  ERROR: Could not install required packages.
        pause
        exit /b 1
    )
    echo  Setup complete!
    echo.
)

:: Run the app (window opens, this terminal closes automatically)
start "" venv\Scripts\pythonw app.py
