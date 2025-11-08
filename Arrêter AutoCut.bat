@echo off
setlocal

echo ========================================
echo     AutoCut - Arret
echo ========================================
echo.

cd /d "%~dp0"

REM Check if PID file exists
if not exist .autocut.pid (
    echo AutoCut n'est pas en cours d'execution ^(fichier PID introuvable^)
    echo.
    pause
    exit /b 0
)

echo Arret des serveurs AutoCut...
echo.

REM Kill processes by window title (for debug mode)
taskkill /FI "WindowTitle eq AutoCut Backend*" /F >nul 2>&1
taskkill /FI "WindowTitle eq AutoCut Frontend*" /F >nul 2>&1

REM Kill processes by port (backend)
echo Verification des processus sur le port 8765...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8765 ^| findstr LISTENING') do (
    echo Arret du processus backend %%a
    taskkill /F /PID %%a >nul 2>&1
)

REM Kill processes by port (frontend)
echo Verification des processus sur le port 5173...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5173 ^| findstr LISTENING') do (
    echo Arret du processus frontend %%a
    taskkill /F /PID %%a >nul 2>&1
)

REM Also kill any Node/Vite processes that might be orphaned
taskkill /F /IM node.exe /FI "WINDOWTITLE eq AutoCut*" >nul 2>&1

REM Remove PID file
del .autocut.pid >nul 2>&1

echo.
echo ========================================
echo   AutoCut arrete avec succes!
echo ========================================
echo.
pause
