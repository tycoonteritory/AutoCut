@echo off
setlocal

echo ========================================
echo     AutoCut - Restarting...
echo ========================================
echo.

cd /d "%~dp0"

REM Stop current instance
echo Stopping current instance...
call "Stop AutoCut.bat"

REM Wait a bit
timeout /t 2 /nobreak >nul

echo.
echo Checking for updates...
git fetch origin >nul 2>&1

REM Check if updates available (simplified check)
git status -uno | findstr "Your branch is behind" >nul
if %errorlevel% equ 0 (
    echo Updates available! Pulling latest changes...
    git pull

    echo Updating dependencies...
    call backend\venv\Scripts\activate.bat
    pip install -q -r backend\requirements.txt

    cd frontend
    call npm install
    cd ..
) else (
    echo Already up to date
)

echo.
echo Starting AutoCut...
call "Start AutoCut.bat"
