@echo off
setlocal

echo ========================================
echo     AutoCut - Stopping...
echo ========================================
echo.

cd /d "%~dp0"

REM Check if PID file exists
if not exist .autocut.pid (
    echo AutoCut is not running ^(no PID file found^)
    echo.
    pause
    exit /b 0
)

echo Stopping AutoCut servers...
echo.

REM Kill processes by window title
taskkill /FI "WindowTitle eq AutoCut Backend*" /F >nul 2>&1
taskkill /FI "WindowTitle eq AutoCut Frontend*" /F >nul 2>&1

REM Kill processes by port
echo Checking for processes on port 8765...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8765 ^| findstr LISTENING') do (
    echo Killing backend process %%a
    taskkill /F /PID %%a >nul 2>&1
)

echo Checking for processes on port 5173...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5173 ^| findstr LISTENING') do (
    echo Killing frontend process %%a
    taskkill /F /PID %%a >nul 2>&1
)

REM Remove PID file
del .autocut.pid >nul 2>&1

echo.
echo ========================================
echo   AutoCut stopped successfully!
echo ========================================
echo.
pause
