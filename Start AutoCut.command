#!/bin/bash

# ============================================
#  🎬 AutoCut - Automatic Video Cutter
# ============================================

# Définir le répertoire du script et se déplacer vers le projet
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Couleurs pour la sortie
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Fonction de nettoyage
cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Arrêt d'AutoCut...${NC}"
    if [ -f ".autocut.pid" ]; then
        while IFS= read -r pid; do
            if ps -p "$pid" > /dev/null 2>&1; then
                kill "$pid" 2>/dev/null
                echo -e "${GREEN}   ✓ Processus $pid arrêté${NC}"
            fi
        done < ".autocut.pid"
        rm -f .autocut.pid
    fi
    echo -e "${GREEN}✅ AutoCut arrêté proprement${NC}"
    echo ""
    echo -e "${CYAN}👋 À bientôt !${NC}"
    exit 0
}

# Capturer Ctrl+C
trap cleanup INT TERM

# Afficher le header
clear
echo -e "${CYAN}${BOLD}"
echo "╔════════════════════════════════════════════════════════╗"
echo "║                                                        ║"
echo "║         🎬  AutoCut - Video Cutter                     ║"
echo "║         Détection automatique des silences            ║"
echo "║                                                        ║"
echo "╚════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

# Vérifier Python
echo -e "${CYAN}[1/6]${NC} ${BOLD}Vérification de Python...${NC}"
PYTHON_CMD=""
if command -v python3.12 &> /dev/null; then
    PYTHON_CMD="python3.12"
    echo -e "${GREEN}      ✓ Python 3.12 trouvé${NC}"
elif command -v python3.11 &> /dev/null; then
    PYTHON_CMD="python3.11"
    echo -e "${GREEN}      ✓ Python 3.11 trouvé${NC}"
elif command -v python3.10 &> /dev/null; then
    PYTHON_CMD="python3.10"
    echo -e "${GREEN}      ✓ Python 3.10 trouvé${NC}"
elif command -v python3.9 &> /dev/null; then
    PYTHON_CMD="python3.9"
    echo -e "${GREEN}      ✓ Python 3.9 trouvé${NC}"
elif command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    if [[ "$PYTHON_VERSION" == "3.14" ]] || [[ "$PYTHON_VERSION" == "3.13" ]]; then
        echo -e "${YELLOW}      ⚠ Python $PYTHON_VERSION détecté - peut causer des problèmes${NC}"
        echo -e "${YELLOW}      Installation de Python 3.12 recommandée: brew install python@3.12${NC}"
        echo ""
        echo -e "${YELLOW}      Appuie sur Entrée pour continuer quand même, ou Ctrl+C pour annuler...${NC}"
        read
    fi
    PYTHON_CMD="python3"
    echo -e "${GREEN}      ✓ Python $(python3 --version | cut -d' ' -f2) trouvé${NC}"
else
    echo -e "${RED}      ✗ Python 3 n'est pas installé !${NC}"
    echo -e "${YELLOW}      Installe Python 3.12 avec Homebrew:${NC}"
    echo -e "${CYAN}        brew install python@3.12${NC}"
    echo ""
    read -p "Appuie sur Entrée pour fermer..."
    exit 1
fi
echo ""

# Vérifier Node.js
echo -e "${CYAN}[2/6]${NC} ${BOLD}Vérification de Node.js...${NC}"
if ! command -v node &> /dev/null; then
    echo -e "${RED}      ✗ Node.js n'est pas installé !${NC}"
    echo -e "${YELLOW}      Télécharge depuis: https://nodejs.org/${NC}"
    echo -e "${YELLOW}      Ou avec Homebrew: brew install node${NC}"
    echo ""
    read -p "Appuie sur Entrée pour fermer..."
    exit 1
fi
NODE_VERSION=$(node --version)
echo -e "${GREEN}      ✓ Node.js $NODE_VERSION trouvé${NC}"
echo ""

# Vérifier FFmpeg
echo -e "${CYAN}[3/6]${NC} ${BOLD}Vérification de FFmpeg...${NC}"
if ! command -v ffmpeg &> /dev/null; then
    echo -e "${RED}      ✗ FFmpeg n'est pas installé !${NC}"
    echo -e "${YELLOW}      Télécharge depuis: https://ffmpeg.org/${NC}"
    echo -e "${YELLOW}      Ou avec Homebrew: brew install ffmpeg${NC}"
    echo ""
    read -p "Appuie sur Entrée pour fermer..."
    exit 1
fi
FFMPEG_VERSION=$(ffmpeg -version 2>&1 | head -n 1 | cut -d' ' -f3)
echo -e "${GREEN}      ✓ FFmpeg $FFMPEG_VERSION trouvé${NC}"
echo ""

# Installer les dépendances Python
echo -e "${CYAN}[4/6]${NC} ${BOLD}Installation des dépendances Python...${NC}"
if [ ! -d "backend/venv" ]; then
    echo -e "${YELLOW}      → Création de l'environnement virtuel...${NC}"
    $PYTHON_CMD -m venv backend/venv
fi

source backend/venv/bin/activate

echo -e "${YELLOW}      → Mise à jour de pip, setuptools et wheel...${NC}"
pip install --upgrade pip setuptools wheel > /dev/null 2>&1

echo -e "${YELLOW}      → Installation des packages Python...${NC}"
pip install -q -r backend/requirements.txt

if [ $? -ne 0 ]; then
    echo -e "${RED}      ✗ Échec de l'installation des dépendances Python${NC}"
    echo -e "${YELLOW}      Nouvelle tentative en mode verbeux...${NC}"
    pip install -r backend/requirements.txt
    read -p "Appuie sur Entrée pour fermer..."
    exit 1
fi

echo -e "${GREEN}      ✓ Dépendances Python installées${NC}"
echo ""

# Installer les dépendances Node.js
echo -e "${CYAN}[5/6]${NC} ${BOLD}Installation des dépendances Node.js...${NC}"
cd frontend
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}      → Installation des packages npm...${NC}"
    npm install > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        echo -e "${RED}      ✗ Échec de l'installation des dépendances Node.js${NC}"
        cd ..
        read -p "Appuie sur Entrée pour fermer..."
        exit 1
    fi
fi
cd ..
echo -e "${GREEN}      ✓ Dépendances Node.js installées${NC}"
echo ""

# Démarrer les serveurs
echo -e "${CYAN}[6/6]${NC} ${BOLD}Démarrage d'AutoCut...${NC}"

# Démarrer le backend
echo -e "${YELLOW}      → Démarrage du backend (port 8765)...${NC}"
source backend/venv/bin/activate
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8765 > backend.log 2>&1 &
BACKEND_PID=$!
echo -e "${GREEN}      ✓ Backend démarré (PID: $BACKEND_PID)${NC}"

# Attendre que le backend soit prêt
sleep 3

# Démarrer le frontend
echo -e "${YELLOW}      → Démarrage du frontend (port 5173)...${NC}"
cd frontend
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..
echo -e "${GREEN}      ✓ Frontend démarré (PID: $FRONTEND_PID)${NC}"
echo ""

# Sauvegarder les PIDs
echo "$BACKEND_PID" > .autocut.pid
echo "$FRONTEND_PID" >> .autocut.pid

# Attendre que les serveurs soient prêts
echo -e "${YELLOW}⏳ Démarrage en cours...${NC}"
sleep 5

# Afficher le message de succès
clear
echo -e "${GREEN}${BOLD}"
echo "╔════════════════════════════════════════════════════════╗"
echo "║                                                        ║"
echo "║         ✅  AutoCut est en cours d'exécution !         ║"
echo "║                                                        ║"
echo "╚════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""
echo -e "${CYAN}${BOLD}📍 Adresses des serveurs :${NC}"
echo -e "${BLUE}   • Backend API:${NC}  http://localhost:8765"
echo -e "${BLUE}   • Frontend UI:${NC}  http://localhost:5173"
echo ""
echo -e "${CYAN}${BOLD}📂 Fichiers de logs :${NC}"
echo -e "${BLUE}   • Backend:${NC}  backend.log"
echo -e "${BLUE}   • Frontend:${NC} frontend.log"
echo ""
echo -e "${MAGENTA}${BOLD}💡 Astuce :${NC}"
echo -e "   Si l'application ne s'ouvre pas automatiquement,"
echo -e "   va sur ${CYAN}http://localhost:5173${NC} dans ton navigateur"
echo ""
echo -e "${YELLOW}${BOLD}🛑 Pour arrêter AutoCut :${NC}"
echo -e "   Appuie sur ${RED}${BOLD}Ctrl+C${NC} dans cette fenêtre"
echo ""
echo -e "${CYAN}════════════════════════════════════════════════════════${NC}"
echo ""

# Ouvrir le navigateur
sleep 2
if command -v open &> /dev/null; then
    open http://localhost:5173
elif command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:5173
fi

echo -e "${GREEN}🚀 AutoCut est prêt à l'emploi !${NC}"
echo ""

# Garder le script actif
wait
