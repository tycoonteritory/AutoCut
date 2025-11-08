@echo off
setlocal enabledelayedexpansion

echo ========================================
echo     AutoCut - Demarrage
echo ========================================
echo.

cd /d "%~dp0"

REM Check if already running
if exist .autocut.pid (
    echo ATTENTION: AutoCut est peut-etre deja en cours d'execution
    echo Si vous etes sur qu'il ne l'est pas, supprimez .autocut.pid et reessayez
    echo.
    pause
    exit /b 1
)

REM Check for Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo ERREUR: Python n'est pas installe ou pas dans PATH
    echo Veuillez installer Python 3.10+ depuis python.org
    echo.
    pause
    exit /b 1
)

echo [OK] Python trouve
python --version

REM Check for Node.js
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo ERREUR: Node.js n'est pas installe ou pas dans PATH
    echo Veuillez installer Node.js depuis nodejs.org
    echo.
    pause
    exit /b 1
)

echo [OK] Node.js trouve
node --version

REM Check for FFmpeg
where ffmpeg >nul 2>nul
if %errorlevel% neq 0 (
    echo ATTENTION: FFmpeg non trouve dans PATH
    echo AutoCut necessite FFmpeg. Installez-le depuis ffmpeg.org
    echo.
    pause
    exit /b 1
)

echo [OK] FFmpeg trouve
echo.

REM Create venv if needed
if not exist "backend\venv" (
    echo Creation de l'environnement virtuel...
    python -m venv backend\venv
)

echo ========================================
echo    Mise a jour des dependances
echo ========================================
echo.

REM Activate venv and install/update dependencies
echo Mise a jour des dependances Python...
call backend\venv\Scripts\activate.bat
python -m pip install --upgrade pip setuptools wheel
pip install -r backend\requirements.txt

REM Install/update Node dependencies
echo Mise a jour des dependances Node.js...
cd frontend
call npm install
cd ..

echo.
echo ========================================
echo    MODE DEBUG ACTIVE
echo ========================================
echo.
echo Les serveurs vont demarrer en mode DEBUG:
echo - Backend: mode reload automatique + logs detailles
echo - Frontend: mode developpement avec logs
echo.
echo Cela reduit l'utilisation d'executables compiles
echo et permet de voir tous les logs en temps reel.
echo.
echo Pour arreter: Utilisez "Arreter AutoCut.bat"
echo.
pause

echo.
echo Demarrage du backend...
echo.

REM Set debug environment
set PYTHONUNBUFFERED=1
set LOG_LEVEL=DEBUG

REM Create PID marker
echo running > .autocut.pid

REM Start backend in a new window with debug mode
start "AutoCut Backend [DEBUG]" cmd /c "cd /d "%~dp0" && call backend\venv\Scripts\activate.bat && python -m uvicorn backend.main:app --host 127.0.0.1 --port 8765 --reload --log-level debug"

REM Wait for backend to start
echo Attente du demarrage du backend...
timeout /t 5 /nobreak >nul

echo Demarrage du frontend...
echo.

REM Start frontend in a new window
start "AutoCut Frontend [DEBUG]" cmd /c "cd /d "%~dp0\frontend" && npm run dev"

REM Wait for frontend to start
timeout /t 5 /nobreak >nul

echo.
echo ========================================
echo   AutoCut est maintenant en cours!
echo.
echo   Backend:  http://localhost:8765
echo   Frontend: http://localhost:5173
echo.
echo   Ouverture du navigateur...
echo ========================================
echo.

REM Open browser
start http://localhost:5173

echo.
echo AutoCut demarre avec succes en MODE DEBUG!
echo.
echo Les fenetres de debug restent ouvertes pour voir les logs.
echo Pour arreter AutoCut, utilisez "Arreter AutoCut.bat"
echo.
echo AVANTAGES DU MODE DEBUG:
echo - Rechargement automatique lors des modifications de code
echo - Logs detailles pour le debogage
echo - Pas besoin de recompiler les executables
echo.
pause
