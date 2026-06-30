@echo off
REM Smart Safety Demo - Windows Launcher
REM Double-click to run, or drag a video file onto this bat.

chcp 65001 >nul 2>&1
cd /d "%~dp0"

echo ============================================================
echo   Smart Safety Demo - Hardhat Detection
echo ============================================================
echo.

echo [1/3] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.9+
    echo         https://www.python.org/downloads/
    pause
    exit /b 1
)
python --version 2>&1
echo.

echo [2/3] Setting up environment...
if not exist "venv\" (
    echo [INFO] First run - creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
)
call venv\Scripts\activate.bat >nul 2>&1
pip install -r requirements.txt -q 2>nul
echo [INFO] Dependencies ready
echo.

echo [3/3] Starting detection...
echo ============================================================
echo   Press 'q' to quit  ^|  Green = SAFE  ^|  Red = UNSAFE
echo ============================================================
echo.

if "%~1"=="" (
    venv\Scripts\python.exe main.py
) else (
    venv\Scripts\python.exe main.py "%~1"
)

echo.
echo [INFO] Program ended. Press any key to close...
pause >nul