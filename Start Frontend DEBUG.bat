@echo off
setlocal

echo ========================================
echo     AutoCut Frontend - DEBUG MODE
echo ========================================
echo.

cd /d "%~dp0"

REM Check for Node.js
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Node.js is not installed
    pause
    exit /b 1
)

echo [OK] Node.js found
node --version
echo.

REM Install dependencies if needed
if not exist "frontend\node_modules" (
    echo Installing Node.js dependencies...
    cd frontend
    call npm install
    cd ..
)

echo ========================================
echo    FRONTEND DEBUG MODE ACTIVE
echo ========================================
echo.
echo This will run the frontend with full debug output
echo.
echo Make sure the backend is running!
echo.
echo To stop: Press Ctrl+C
echo.
pause

echo.
echo Starting frontend in DEBUG mode...
echo.

cd frontend

echo ========================================
echo    FRONTEND DEBUG OUTPUT
echo ========================================
echo.

REM Run in dev mode (foreground)
call npm run dev

echo.
echo Frontend stopped
pause
