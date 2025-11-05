@echo off
echo ========================================
echo      AutoCut - Automatic Video Cutter
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed!
    echo Please install Python 3.8 or higher from https://www.python.org/
    pause
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js is not installed!
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

REM Check if FFmpeg is installed
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] FFmpeg is not installed!
    echo Please install FFmpeg from https://ffmpeg.org/
    echo.
    echo Quick install with Chocolatey: choco install ffmpeg
    pause
    exit /b 1
)

echo [OK] All dependencies are installed!
echo.

REM Install Python dependencies
echo [1/4] Installing Python dependencies...
if not exist "backend\venv" (
    echo Creating virtual environment...
    python -m venv backend\venv
)

call backend\venv\Scripts\activate
pip install -r backend\requirements.txt >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Failed to install Python dependencies
    pause
    exit /b 1
)
echo [OK] Python dependencies installed
echo.

REM Install Node.js dependencies
echo [2/4] Installing Node.js dependencies...
cd frontend
if not exist "node_modules" (
    call npm install
    if errorlevel 1 (
        echo [ERROR] Failed to install Node.js dependencies
        cd ..
        pause
        exit /b 1
    )
)
cd ..
echo [OK] Node.js dependencies installed
echo.

REM Start backend server
echo [3/4] Starting backend server on port 8765...
start "AutoCut Backend" cmd /k "cd /d %~dp0.. && backend\venv\Scripts\activate && python -m uvicorn backend.main:app --host 127.0.0.1 --port 8765"

REM Wait a bit for backend to start
timeout /t 3 >nul

REM Start frontend server
echo [4/4] Starting frontend server on port 5173...
start "AutoCut Frontend" cmd /k "cd /d %~dp0..\frontend && npm run dev"

echo.
echo ========================================
echo   AutoCut is starting...
echo
echo   Backend:  http://localhost:8765
echo   Frontend: http://localhost:5173
echo
echo   Opening browser in 5 seconds...
echo ========================================
echo.

timeout /t 5 >nul

REM Open browser
start http://localhost:5173

echo.
echo AutoCut is now running!
echo Close this window to keep the servers running.
echo To stop AutoCut, close the Backend and Frontend windows.
echo.
pause
