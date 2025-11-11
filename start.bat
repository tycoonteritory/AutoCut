@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

REM ============================================
REM  🎬 AutoCut - Lanceur Unifié pour Windows
REM ============================================

REM Se déplacer dans le dossier du script
cd /d "%~dp0"

REM Variables pour les PIDs
set BACKEND_PID=
set FRONTEND_PID=

REM Header
cls
echo.
echo ╔════════════════════════════════════════════════════════╗
echo ║                                                        ║
echo ║         🎬  AutoCut - Video Cutter                     ║
echo ║         Détection automatique des silences            ║
echo ║                                                        ║
echo ╚════════════════════════════════════════════════════════╝
echo.
echo.

REM Étape 1: Vérifier Python
echo [1/6] Vérification de Python...
set PYTHON_CMD=

where python >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
    set PYTHON_CMD=python
    echo       ✓ Python !PYTHON_VERSION! trouvé
) else (
    echo       ✗ Python n'est pas installé !
    echo       Téléchargez Python depuis : https://www.python.org/downloads/
    echo       Assurez-vous de cocher "Add Python to PATH" lors de l'installation
    echo.
    pause
    exit /b 1
)
echo.

REM Étape 2: Vérifier Node.js
echo [2/6] Vérification de Node.js...
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo       ✗ Node.js n'est pas installé !
    echo       Téléchargez Node.js depuis : https://nodejs.org/
    echo.
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('node --version') do set NODE_VERSION=%%i
echo       ✓ Node.js !NODE_VERSION! trouvé
echo.

REM Étape 3: Vérifier FFmpeg
echo [3/6] Vérification de FFmpeg...
where ffmpeg >nul 2>&1
if %errorlevel% neq 0 (
    echo       ✗ FFmpeg n'est pas installé !
    echo       Téléchargez FFmpeg depuis : https://ffmpeg.org/download.html
    echo       Ou installez avec Chocolatey : choco install ffmpeg
    echo.
    pause
    exit /b 1
)
for /f "tokens=3" %%i in ('ffmpeg -version 2^>^&1 ^| findstr /C:"ffmpeg version"') do set FFMPEG_VERSION=%%i
echo       ✓ FFmpeg !FFMPEG_VERSION! trouvé
echo.

REM Étape 4: Créer et activer l'environnement virtuel Python
echo [4/6] Configuration de l'environnement Python...

if not exist "backend\venv" (
    echo       → Création de l'environnement virtuel...
    !PYTHON_CMD! -m venv backend\venv
    if %errorlevel% neq 0 (
        echo       ✗ Échec de la création de l'environnement virtuel
        pause
        exit /b 1
    )
)

REM Activer l'environnement virtuel
call backend\venv\Scripts\activate.bat

REM Mettre à jour pip et installer les dépendances
echo       → Mise à jour de pip...
python -m pip install --quiet --upgrade pip setuptools wheel

echo       → Installation des dépendances Python...
echo       (Cela peut prendre plusieurs minutes...)
echo.

REM Déterminer quel fichier requirements utiliser
set REQUIREMENTS_FILE=backend\requirements.txt
if exist "backend\requirements_windows.txt" (
    set REQUIREMENTS_FILE=backend\requirements_windows.txt
    echo       ℹ️  Utilisation de requirements_windows.txt
)

REM Première tentative d'installation silencieuse
pip install --quiet -r !REQUIREMENTS_FILE! > pip_install.log 2>&1
if %errorlevel% neq 0 (
    echo.
    echo       ⚠️  Certaines dépendances ont échoué
    echo       → Tentative d'installation en mode verbeux...
    echo.

    REM Afficher les erreurs
    type pip_install.log | findstr /C:"error" /C:"ERROR" /C:"failed" /C:"FAILED"
    echo.

    REM Vérifier si c'est openai-whisper qui pose problème
    type pip_install.log | findstr /C:"openai-whisper" >nul 2>&1
    if !errorlevel! equ 0 (
        echo       ════════════════════════════════════════════════
        echo       ⚠️  PROBLÈME DÉTECTÉ : openai-whisper
        echo       ════════════════════════════════════════════════
        echo.
        echo       openai-whisper nécessite Visual Studio Build Tools
        echo.
        echo       SOLUTIONS :
        echo.
        echo       1. Installer Visual Studio Build Tools
        echo          https://visualstudio.microsoft.com/visual-cpp-build-tools/
        echo.
        echo       2. Consulter le guide détaillé :
        echo          Ouvrez INSTALL_WINDOWS.md
        echo.
        echo       3. Continuer SANS openai-whisper ^(non recommandé^)
        echo          Les fonctionnalités de transcription ne seront pas disponibles
        echo.
        echo       ════════════════════════════════════════════════
        echo.

        choice /C 123 /N /M "Choisissez une option (1, 2 ou 3) : "
        if !errorlevel! equ 1 (
            echo.
            echo       Veuillez installer Visual Studio Build Tools, puis relancez start.bat
            start https://visualstudio.microsoft.com/visual-cpp-build-tools/
            pause
            exit /b 1
        )
        if !errorlevel! equ 2 (
            echo.
            echo       Ouverture du guide d'installation...
            if exist "INSTALL_WINDOWS.md" (
                start notepad INSTALL_WINDOWS.md
            ) else (
                echo       Fichier INSTALL_WINDOWS.md non trouvé
            )
            pause
            exit /b 1
        )
        if !errorlevel! equ 3 (
            echo.
            echo       ⚠️  Continuation sans openai-whisper...
            echo       → Installation des autres dépendances...

            REM Créer un requirements temporaire sans openai-whisper
            findstr /V /C:"openai-whisper" !REQUIREMENTS_FILE! > backend\requirements_temp.txt
            pip install -r backend\requirements_temp.txt
            del backend\requirements_temp.txt

            if !errorlevel! neq 0 (
                echo       ✗ Échec de l'installation des autres dépendances
                pause
                exit /b 1
            )

            echo.
            echo       ✓ Dépendances installées ^(sauf openai-whisper^)
            echo       ⚠️  Les fonctionnalités de transcription ne sont pas disponibles
        )
    ) else (
        REM Autre type d'erreur
        echo       → Nouvelle tentative complète...
        pip install -r !REQUIREMENTS_FILE!
        if !errorlevel! neq 0 (
            echo.
            echo       ✗ Échec de l'installation
            echo       Consultez pip_install.log pour plus de détails
            pause
            exit /b 1
        )
    )
)

echo       ✓ Environnement Python configuré
echo.

REM Étape 5: Installer les dépendances Node.js
echo [5/6] Installation des dépendances Node.js...

cd frontend
if not exist "node_modules" (
    echo       → Installation des packages npm...
    call npm install --silent
    if %errorlevel% neq 0 (
        echo       ✗ Échec de l'installation des dépendances Node.js
        cd ..
        pause
        exit /b 1
    )
) else (
    echo       ✓ Packages npm déjà installés
)
cd ..

echo       ✓ Dépendances Node.js OK
echo.

REM Étape 6: Démarrer les serveurs
echo [6/6] Démarrage d'AutoCut...
echo.

REM Démarrer le backend
echo       → Démarrage du backend (port 8765)...
call backend\venv\Scripts\activate.bat
set PYTHONUNBUFFERED=1

REM Lancer le backend en background
start /B python -m uvicorn backend.main:app --host 127.0.0.1 --port 8765 > backend.log 2>&1

echo       ✓ Backend démarré

REM Attendre que le backend soit prêt
echo       → Vérification du backend...
set BACKEND_READY=0
for /L %%i in (1,1,15) do (
    timeout /t 1 /nobreak >nul
    curl -s http://localhost:8765/health >nul 2>&1
    if !errorlevel! equ 0 (
        set BACKEND_READY=1
        goto backend_ready
    )
    echo|set /p="      ."
)
:backend_ready
echo.

if !BACKEND_READY! equ 0 (
    echo       ✗ Le backend n'a pas démarré correctement
    echo       Vérifiez le fichier backend.log pour plus d'infos
    type backend.log
    pause
    exit /b 1
)

echo       ✓ Backend opérationnel
echo.

REM Démarrer le frontend
echo       → Démarrage du frontend (port 5173)...
cd frontend
start /B cmd /c "npm run dev > ..\frontend.log 2>&1"
cd ..

echo       ✓ Frontend démarré

REM Attendre que le frontend soit prêt
echo       → Vérification du frontend...
set FRONTEND_READY=0
for /L %%i in (1,1,10) do (
    timeout /t 1 /nobreak >nul
    curl -s http://localhost:5173 >nul 2>&1
    if !errorlevel! equ 0 (
        set FRONTEND_READY=1
        goto frontend_ready
    )
    echo|set /p="      ."
)
:frontend_ready
echo.

if !FRONTEND_READY! equ 0 (
    echo       ⚠️  Le frontend prend du temps à démarrer (normal)
)

echo       ✓ Frontend en cours de démarrage
echo.

REM Message de succès
timeout /t 2 /nobreak >nul
cls

echo.
echo ╔════════════════════════════════════════════════════════╗
echo ║                                                        ║
echo ║         ✅  AutoCut est en cours d'exécution !         ║
echo ║                                                        ║
echo ╚════════════════════════════════════════════════════════╝
echo.
echo.
echo 📍 Adresses des serveurs :
echo    • Backend API:  http://localhost:8765
echo    • Frontend UI:  http://localhost:5173
echo.
echo 📂 Fichiers de logs :
echo    • Backend:  backend.log
echo    • Frontend: frontend.log
echo.
echo 💡 Astuce :
echo    Si l'application ne s'ouvre pas automatiquement,
echo    ouvrez http://localhost:5173 dans votre navigateur
echo.
echo 🛑 Pour arrêter AutoCut :
echo    Fermez cette fenêtre ou appuyez sur Ctrl+C
echo.
echo ════════════════════════════════════════════════════════
echo.

REM Ouvrir le navigateur
timeout /t 2 /nobreak >nul
start http://localhost:5173

echo 🚀 AutoCut est prêt à l'emploi !
echo.
echo 📊 Les serveurs sont en cours d'exécution...
echo    Gardez cette fenêtre ouverte
echo.

REM Attendre que l'utilisateur ferme la fenêtre
pause
