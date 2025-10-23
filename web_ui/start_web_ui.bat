@echo off
echo Starting Smart RAG Web UI...
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.13.3 or higher
    pause
    exit /b 1
)

REM Start the web server
python server.py --port 8080

pause
