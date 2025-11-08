#!/bin/bash

# ============================================
#  🎬 AutoCut - Lanceur Unifié et Robuste
# ============================================

# Se déplacer dans le dossier du script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m'

# Variables pour les PIDs
BACKEND_PID=""
FRONTEND_PID=""

# Fonction de nettoyage
cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Arrêt d'AutoCut...${NC}"

    # Arrêter le frontend
    if [ -n "$FRONTEND_PID" ] && ps -p $FRONTEND_PID > /dev/null 2>&1; then
        echo -e "${BLUE}   → Arrêt du frontend (PID: $FRONTEND_PID)${NC}"
        kill $FRONTEND_PID 2>/dev/null
        wait $FRONTEND_PID 2>/dev/null
    fi

    # Arrêter le backend
    if [ -n "$BACKEND_PID" ] && ps -p $BACKEND_PID > /dev/null 2>&1; then
        echo -e "${BLUE}   → Arrêt du backend (PID: $BACKEND_PID)${NC}"
        kill $BACKEND_PID 2>/dev/null
        wait $BACKEND_PID 2>/dev/null
    fi

    # Nettoyer les fichiers de log et PID
    rm -f .autocut.pid backend.log frontend.log

    echo -e "${GREEN}✅ AutoCut arrêté proprement${NC}"
    echo ""
    echo -e "${CYAN}👋 À bientôt !${NC}"
    exit 0
}

# Intercepter Ctrl+C et autres signaux
trap cleanup EXIT INT TERM

# Header
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

# Étape 1: Vérifier Python
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
    PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
    PYTHON_CMD="python3"
    echo -e "${GREEN}      ✓ Python $PYTHON_VERSION trouvé${NC}"
else
    echo -e "${RED}      ✗ Python 3 n'est pas installé !${NC}"
    echo -e "${YELLOW}      Installez Python avec :${NC}"
    echo -e "${CYAN}        brew install python@3.12${NC}"
    echo ""
    read -p "Appuyez sur Entrée pour fermer..."
    exit 1
fi
echo ""

# Étape 2: Vérifier Node.js
echo -e "${CYAN}[2/6]${NC} ${BOLD}Vérification de Node.js...${NC}"
if ! command -v node &> /dev/null; then
    echo -e "${RED}      ✗ Node.js n'est pas installé !${NC}"
    echo -e "${YELLOW}      Installez Node.js avec :${NC}"
    echo -e "${CYAN}        brew install node${NC}"
    echo ""
    read -p "Appuyez sur Entrée pour fermer..."
    exit 1
fi
NODE_VERSION=$(node --version)
echo -e "${GREEN}      ✓ Node.js $NODE_VERSION trouvé${NC}"
echo ""

# Étape 3: Vérifier FFmpeg
echo -e "${CYAN}[3/6]${NC} ${BOLD}Vérification de FFmpeg...${NC}"
if ! command -v ffmpeg &> /dev/null; then
    echo -e "${RED}      ✗ FFmpeg n'est pas installé !${NC}"
    echo -e "${YELLOW}      Installez FFmpeg avec :${NC}"
    echo -e "${CYAN}        brew install ffmpeg${NC}"
    echo ""
    read -p "Appuyez sur Entrée pour fermer..."
    exit 1
fi
FFMPEG_VERSION=$(ffmpeg -version 2>&1 | head -n 1 | cut -d' ' -f3)
echo -e "${GREEN}      ✓ FFmpeg $FFMPEG_VERSION trouvé${NC}"
echo ""

# Étape 4: Créer et activer l'environnement virtuel Python
echo -e "${CYAN}[4/6]${NC} ${BOLD}Configuration de l'environnement Python...${NC}"

if [ ! -d "backend/venv" ]; then
    echo -e "${YELLOW}      → Création de l'environnement virtuel...${NC}"
    $PYTHON_CMD -m venv backend/venv
    if [ $? -ne 0 ]; then
        echo -e "${RED}      ✗ Échec de la création de l'environnement virtuel${NC}"
        exit 1
    fi
fi

# Activer l'environnement virtuel
source backend/venv/bin/activate

# Mettre à jour pip et installer les dépendances
echo -e "${YELLOW}      → Mise à jour de pip...${NC}"
pip install --quiet --upgrade pip setuptools wheel

echo -e "${YELLOW}      → Installation des dépendances Python...${NC}"
pip install --quiet -r backend/requirements.txt

if [ $? -ne 0 ]; then
    echo -e "${RED}      ✗ Échec de l'installation des dépendances Python${NC}"
    echo -e "${YELLOW}      Nouvelle tentative en mode verbeux...${NC}"
    pip install -r backend/requirements.txt
    if [ $? -ne 0 ]; then
        read -p "Appuyez sur Entrée pour fermer..."
        exit 1
    fi
fi

echo -e "${GREEN}      ✓ Environnement Python configuré${NC}"
echo ""

# Étape 5: Installer les dépendances Node.js
echo -e "${CYAN}[5/6]${NC} ${BOLD}Installation des dépendances Node.js...${NC}"

cd frontend
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}      → Installation des packages npm...${NC}"
    npm install --silent
    if [ $? -ne 0 ]; then
        echo -e "${RED}      ✗ Échec de l'installation des dépendances Node.js${NC}"
        cd ..
        read -p "Appuyez sur Entrée pour fermer..."
        exit 1
    fi
else
    echo -e "${GREEN}      ✓ Packages npm déjà installés${NC}"
fi
cd ..

echo -e "${GREEN}      ✓ Dépendances Node.js OK${NC}"
echo ""

# Étape 6: Démarrer les serveurs
echo -e "${CYAN}[6/6]${NC} ${BOLD}Démarrage d'AutoCut...${NC}"
echo ""

# Démarrer le backend
echo -e "${YELLOW}      → Démarrage du backend (port 8765)...${NC}"
source backend/venv/bin/activate
export PYTHONUNBUFFERED=1

# Lancer le backend en background avec logs
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8765 > backend.log 2>&1 &
BACKEND_PID=$!

# Sauvegarder le PID immédiatement
echo "$BACKEND_PID" > .autocut.pid

echo -e "${GREEN}      ✓ Backend démarré (PID: $BACKEND_PID)${NC}"

# Attendre que le backend soit prêt
echo -e "${YELLOW}      → Vérification du backend...${NC}"
BACKEND_READY=false
for i in {1..15}; do
    sleep 1
    if curl -s http://localhost:8765/api/ > /dev/null 2>&1; then
        BACKEND_READY=true
        break
    fi
    echo -ne "      ${YELLOW}.${NC}"
done
echo ""

if [ "$BACKEND_READY" = false ]; then
    echo -e "${RED}      ✗ Le backend n'a pas démarré correctement${NC}"
    echo -e "${YELLOW}      Vérifiez le fichier backend.log pour plus d'infos${NC}"
    cat backend.log
    exit 1
fi

echo -e "${GREEN}      ✓ Backend opérationnel${NC}"
echo ""

# Démarrer le frontend
echo -e "${YELLOW}      → Démarrage du frontend (port 5173)...${NC}"
cd frontend
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

# Ajouter le PID du frontend
echo "$FRONTEND_PID" >> .autocut.pid

echo -e "${GREEN}      ✓ Frontend démarré (PID: $FRONTEND_PID)${NC}"

# Attendre que le frontend soit prêt
echo -e "${YELLOW}      → Vérification du frontend...${NC}"
FRONTEND_READY=false
for i in {1..10}; do
    sleep 1
    if curl -s http://localhost:5173 > /dev/null 2>&1; then
        FRONTEND_READY=true
        break
    fi
    echo -ne "      ${YELLOW}.${NC}"
done
echo ""

if [ "$FRONTEND_READY" = false ]; then
    echo -e "${YELLOW}      ⚠️  Le frontend prend du temps à démarrer (normal)${NC}"
fi

echo -e "${GREEN}      ✓ Frontend en cours de démarrage${NC}"
echo ""

# Message de succès
sleep 2
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
echo -e "${CYAN}${BOLD}🔧 Informations de débogage :${NC}"
echo -e "${BLUE}   • Backend PID:${NC}  $BACKEND_PID"
echo -e "${BLUE}   • Frontend PID:${NC} $FRONTEND_PID"
echo ""
echo -e "${MAGENTA}${BOLD}💡 Astuce :${NC}"
echo -e "   Si l'application ne s'ouvre pas automatiquement,"
echo -e "   ouvrez ${CYAN}http://localhost:5173${NC} dans votre navigateur"
echo ""
echo -e "${YELLOW}${BOLD}🛑 Pour arrêter AutoCut :${NC}"
echo -e "   Appuyez sur ${RED}${BOLD}Ctrl+C${NC} dans cette fenêtre"
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
echo -e "${BLUE}📊 Affichage des logs...${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════${NC}"
echo ""

# Afficher les logs en temps réel (dernières lignes)
tail -f backend.log &
TAIL_PID=$!

# Attendre l'arrêt
wait $BACKEND_PID $FRONTEND_PID

# Nettoyer le tail
kill $TAIL_PID 2>/dev/null

# Le cleanup sera appelé automatiquement grâce au trap
