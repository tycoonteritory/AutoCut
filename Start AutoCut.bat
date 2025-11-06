@echo off
setlocal enabledelayedexpansion

echo ========================================
echo     AutoCut - Starting...
echo ========================================
echo.

cd /d "%~dp0"

REM Check if already running
if exist .autocut.pid (
    echo WARNING: AutoCut may already be running
    echo If you're sure it's not, delete .autocut.pid and try again
    echo.
    pause
    exit /b 1
)

REM Check for Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.10+ from python.org
    echo.
    pause
    exit /b 1
)

echo [OK] Python found
python --version

REM Check for Node.js
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Node.js is not installed or not in PATH
    echo Please install Node.js from nodejs.org
    echo.
    pause
    exit /b 1
)

echo [OK] Node.js found
node --version

REM Check for FFmpeg
where ffmpeg >nul 2>nul
if %errorlevel% neq 0 (
    echo WARNING: FFmpeg not found in PATH
    echo AutoCut needs FFmpeg. Install from ffmpeg.org
    echo.
    pause
    exit /b 1
)

echo [OK] FFmpeg found
echo.

REM Create venv if needed
if not exist "backend\venv" (
    echo Creating virtual environment...
    python -m venv backend\venv
)

REM Activate venv and install dependencies
echo Installing Python dependencies...
call backend\venv\Scripts\activate.bat
python -m pip install --upgrade pip setuptools wheel >nul 2>&1
pip install -r backend\requirements.txt >nul 2>&1

REM Install Node dependencies if needed
if not exist "frontend\node_modules" (
    echo Installing Node.js dependencies...
    cd frontend
    call npm install
    cd ..
)

REM Start backend
echo.
echo Starting backend server...
start "AutoCut Backend" /min cmd /c "call backend\venv\Scripts\activate.bat && python -m uvicorn backend.main:app --host 127.0.0.1 --port 8765 > backend.log 2>&1"

REM Wait a bit
timeout /t 3 /nobreak >nul

REM Start frontend
echo Starting frontend server...
cd frontend
start "AutoCut Frontend" /min cmd /c "npm run dev > ..\frontend.log 2>&1"
cd ..

REM Create PID marker
echo running > .autocut.pid

REM Wait a bit more
timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo   AutoCut is now running!
echo.
echo   Backend:  http://localhost:8765
echo   Frontend: http://localhost:5173
echo.
echo   Opening browser...
echo ========================================
echo.

REM Open browser
start http://localhost:5173

echo.
echo AutoCut started successfully!
echo.
echo To stop AutoCut, double-click "Stop AutoCut.bat"
echo To restart AutoCut, double-click "Restart AutoCut.bat"
echo.
echo Logs are saved in:
echo   - backend.log
echo   - frontend.log
echo.
pause
