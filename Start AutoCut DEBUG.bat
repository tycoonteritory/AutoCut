@echo off
setlocal

echo ========================================
echo     AutoCut - DEBUG MODE
echo ========================================
echo.

cd /d "%~dp0"

REM Check if already running
if exist .autocut.pid (
    echo WARNING: AutoCut may already be running
    echo Please stop it first with "Stop AutoCut.bat"
    echo.
    pause
    exit /b 1
)

REM Check for Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed
    pause
    exit /b 1
)

echo [OK] Python found
python --version

REM Create venv if needed
if not exist "backend\venv" (
    echo Creating virtual environment...
    python -m venv backend\venv
)

REM Install dependencies
echo Installing Python dependencies...
call backend\venv\Scripts\activate.bat
python -m pip install --upgrade pip setuptools wheel >nul
pip install -r backend\requirements.txt

if not exist "frontend\node_modules" (
    echo Installing Node.js dependencies...
    cd frontend
    call npm install
    cd ..
)

echo.
echo ========================================
echo    DEBUG MODE ACTIVE
echo ========================================
echo.
echo This will run the backend in FOREGROUND with full logging
echo You'll see all debug output in this terminal
echo.
echo To stop: Press Ctrl+C
echo.
pause

echo.
echo Starting backend in DEBUG mode...
echo.

REM Set debug environment
set PYTHONUNBUFFERED=1
set LOG_LEVEL=DEBUG

REM Start backend in foreground (current window)
call backend\venv\Scripts\activate.bat

echo ========================================
echo    BACKEND DEBUG OUTPUT
echo ========================================
echo.

REM Run with reload for auto-restart on code changes
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8765 --reload --log-level debug

echo.
echo Backend stopped
pause
