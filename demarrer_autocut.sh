#!/bin/bash

echo "========================================"
echo "    AutoCut - Démarrage"
echo "========================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if already running
if [ -f ".autocut.pid" ]; then
    echo -e "${YELLOW}[ATTENTION] AutoCut est peut-être déjà en cours d'exécution${NC}"
    echo "Si vous êtes sûr qu'il ne l'est pas, supprimez .autocut.pid et réessayez"
    echo ""
    exit 1
fi

# Check for Python - prefer 3.12, then 3.11, then 3.10, then 3.9, then default
PYTHON_CMD=""
if command -v python3.12 &> /dev/null; then
    PYTHON_CMD="python3.12"
    echo -e "${GREEN}[OK] Python 3.12 trouvé${NC}"
elif command -v python3.11 &> /dev/null; then
    PYTHON_CMD="python3.11"
    echo -e "${GREEN}[OK] Python 3.11 trouvé${NC}"
elif command -v python3.10 &> /dev/null; then
    PYTHON_CMD="python3.10"
    echo -e "${GREEN}[OK] Python 3.10 trouvé${NC}"
elif command -v python3.9 &> /dev/null; then
    PYTHON_CMD="python3.9"
    echo -e "${GREEN}[OK] Python 3.9 trouvé${NC}"
elif command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    if [[ "$PYTHON_VERSION" == "3.14" ]] || [[ "$PYTHON_VERSION" == "3.13" ]]; then
        echo -e "${YELLOW}[ATTENTION] Python $PYTHON_VERSION détecté - cela peut causer des problèmes de compatibilité${NC}"
        echo "L'installation de Python 3.12 est recommandée:"
        echo "  brew install python@3.12"
        echo ""
        echo "Appuyez sur Entrée pour continuer quand même, ou Ctrl+C pour annuler..."
        read
    fi
    PYTHON_CMD="python3"
    echo -e "${GREEN}[OK] Python $(python3 --version) trouvé${NC}"
else
    echo -e "${RED}[ERREUR] Python 3 n'est pas installé!${NC}"
    echo "Veuillez installer Python 3.12:"
    echo "  brew install python@3.12  (macOS)"
    echo "  apt install python3.12     (Linux)"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${RED}[ERREUR] Node.js n'est pas installé!${NC}"
    echo "Veuillez installer Node.js depuis https://nodejs.org/"
    echo "Ou utilisez: brew install node (macOS)"
    exit 1
fi

echo -e "${GREEN}[OK] Node.js trouvé${NC}"
node --version

# Check if FFmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    echo -e "${RED}[ERREUR] FFmpeg n'est pas installé!${NC}"
    echo "Veuillez installer FFmpeg depuis https://ffmpeg.org/"
    echo "Ou utilisez: brew install ffmpeg (macOS)"
    exit 1
fi

echo -e "${GREEN}[OK] FFmpeg trouvé${NC}"
echo ""

# Create venv if needed
if [ ! -d "backend/venv" ]; then
    echo "Création de l'environnement virtuel..."
    $PYTHON_CMD -m venv backend/venv
fi

echo "========================================"
echo "    Mise à jour des dépendances"
echo "========================================"
echo ""

# Install Python dependencies
echo "Mise à jour des dépendances Python..."
source backend/venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r backend/requirements.txt

if [ $? -ne 0 ]; then
    echo -e "${RED}[ERREUR] Échec de l'installation des dépendances Python${NC}"
    exit 1
fi

echo -e "${GREEN}[OK] Dépendances Python à jour${NC}"

# Install Node.js dependencies
echo "Mise à jour des dépendances Node.js..."
cd frontend
npm install
if [ $? -ne 0 ]; then
    echo -e "${RED}[ERREUR] Échec de l'installation des dépendances Node.js${NC}"
    cd ..
    exit 1
fi
cd ..

echo -e "${GREEN}[OK] Dépendances Node.js à jour${NC}"
echo ""

echo "========================================"
echo "    MODE DEBUG ACTIF"
echo "========================================"
echo ""
echo "Les serveurs vont démarrer en mode DEBUG:"
echo "- Backend: mode reload automatique + logs détaillés"
echo "- Frontend: mode développement avec logs"
echo ""
echo "Cela réduit l'utilisation d'exécutables compilés"
echo "et permet de voir tous les logs en temps réel."
echo ""
echo "Pour arrêter: Utilisez ./arreter_autocut.sh"
echo ""
echo "Appuyez sur Entrée pour continuer..."
read

echo ""
echo "Démarrage du backend..."
echo ""

# Set debug environment
export PYTHONUNBUFFERED=1
export LOG_LEVEL=DEBUG

# Start backend with debug mode in a new terminal
source backend/venv/bin/activate

# For macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    osascript -e 'tell app "Terminal" to do script "cd '"$SCRIPT_DIR"' && source backend/venv/bin/activate && python -m uvicorn backend.main:app --host 127.0.0.1 --port 8765 --reload --log-level debug"' &
    BACKEND_PID=$!
# For Linux
else
    gnome-terminal -- bash -c "cd '$SCRIPT_DIR' && source backend/venv/bin/activate && python -m uvicorn backend.main:app --host 127.0.0.1 --port 8765 --reload --log-level debug; exec bash" &
    BACKEND_PID=$!
fi

echo "Attente du démarrage du backend..."
sleep 5

echo "Démarrage du frontend..."
echo ""

# Start frontend in a new terminal
# For macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    osascript -e 'tell app "Terminal" to do script "cd '"$SCRIPT_DIR/frontend"' && npm run dev"' &
    FRONTEND_PID=$!
# For Linux
else
    gnome-terminal -- bash -c "cd '$SCRIPT_DIR/frontend' && npm run dev; exec bash" &
    FRONTEND_PID=$!
fi

echo "Attente du démarrage du frontend..."
sleep 5

echo ""
echo "========================================"
echo "  AutoCut est maintenant en cours!"
echo ""
echo "  Backend:  http://localhost:8765"
echo "  Frontend: http://localhost:5173"
echo ""
echo "  Ouverture du navigateur..."
echo "========================================"
echo ""

# Save PIDs to file
echo "$BACKEND_PID" > .autocut.pid
echo "$FRONTEND_PID" >> .autocut.pid

# Open browser
if command -v open &> /dev/null; then
    open http://localhost:5173
elif command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:5173
fi

echo ""
echo -e "${GREEN}AutoCut démarré avec succès en MODE DEBUG!${NC}"
echo ""
echo "Les fenêtres de debug restent ouvertes pour voir les logs."
echo "Pour arrêter AutoCut, utilisez: ./arreter_autocut.sh"
echo ""
echo -e "${BLUE}AVANTAGES DU MODE DEBUG:${NC}"
echo "- Rechargement automatique lors des modifications de code"
echo "- Logs détaillés pour le débogage"
echo "- Pas besoin de recompiler les exécutables"
echo ""
