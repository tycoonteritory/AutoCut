#!/bin/bash

# ============================================
#  🎬 AutoCut - Script Unique de Gestion
# ============================================
# Démarre backend + frontend avec logs en direct
# Appuyez sur Entrée pour tout arrêter proprement
# ============================================

# Aller dans le dossier du script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# PIDs des processus
BACKEND_PID=""
FRONTEND_PID=""

# Fonction de nettoyage
cleanup() {
    echo ""
    echo -e "${YELLOW}⚠️  Arrêt d'AutoCut...${NC}"
    
    if [ -n "$BACKEND_PID" ] && ps -p $BACKEND_PID > /dev/null 2>&1; then
        echo -e "${BLUE}   → Arrêt du backend (PID: $BACKEND_PID)${NC}"
        kill $BACKEND_PID 2>/dev/null
        wait $BACKEND_PID 2>/dev/null
    fi
    
    if [ -n "$FRONTEND_PID" ] && ps -p $FRONTEND_PID > /dev/null 2>&1; then
        echo -e "${BLUE}   → Arrêt du frontend (PID: $FRONTEND_PID)${NC}"
        kill $FRONTEND_PID 2>/dev/null
        wait $FRONTEND_PID 2>/dev/null
    fi
    
    rm -f .autocut.pid
    echo -e "${GREEN}✅ AutoCut arrêté proprement${NC}"
    echo ""
    exit 0
}

trap cleanup EXIT INT TERM

clear
echo -e "${CYAN}"
echo "╔════════════════════════════════════════╗"
echo "║     🎬  AutoCut - Lanceur Unique       ║"
echo "╚════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

echo -e "${MAGENTA}📋 Vérification des dépendances...${NC}"
echo ""

# Python
PYTHON_CMD=""
if command -v python3.12 &> /dev/null; then
    PYTHON_CMD="python3.12"
elif command -v python3.11 &> /dev/null; then
    PYTHON_CMD="python3.11"
elif command -v python3.10 &> /dev/null; then
    PYTHON_CMD="python3.10"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    echo -e "${RED}❌ Python 3 introuvable !${NC}"
    echo "   Installez avec : brew install python@3.12"
    exit 1
fi
echo -e "${GREEN}✓ Python trouvé${NC} : $PYTHON_CMD"

# Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js introuvable !${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Node.js trouvé${NC} : $(node --version)"

# FFmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo -e "${RED}❌ FFmpeg introuvable !${NC}"
    exit 1
fi
echo -e "${GREEN}✓ FFmpeg trouvé${NC}"

echo ""
echo -e "${MAGENTA}🔧 Préparation...${NC}"
echo ""

if [ ! -d "backend/venv" ]; then
    echo "   → Création de l'environnement virtuel..."
    $PYTHON_CMD -m venv backend/venv
    echo -e "${GREEN}   ✓ Environnement créé${NC}"
fi

source backend/venv/bin/activate

echo "   → Vérification des packages Python..."
NEED_INSTALL=false
python -c "import fastapi" 2>/dev/null || NEED_INSTALL=true

if [ "$NEED_INSTALL" = true ]; then
    echo -e "${YELLOW}   ⚠️  Installation des packages...${NC}"
    pip install -q --upgrade pip
    pip install -q -r backend/requirements.txt
    echo -e "${GREEN}   ✓ Packages installés${NC}"
else
    echo -e "${GREEN}   ✓ Packages OK${NC}"
fi

if [ ! -d "frontend/node_modules" ]; then
    echo "   → Installation des packages Node.js..."
    cd frontend && npm install --silent && cd ..
    echo -e "${GREEN}   ✓ Packages installés${NC}"
else
    echo -e "${GREEN}   ✓ Packages Node.js OK${NC}"
fi

echo ""
echo -e "${MAGENTA}🚀 Démarrage des serveurs...${NC}"
echo ""

echo -e "${BLUE}   → Démarrage du backend...${NC}"
source backend/venv/bin/activate
export PYTHONUNBUFFERED=1
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8765 2>&1 | sed 's/^/   [BACKEND] /' &
BACKEND_PID=$!

sleep 3

MAX_RETRIES=10
RETRY_COUNT=0
BACKEND_OK=false

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:8765/health > /dev/null 2>&1; then
        BACKEND_OK=true
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    sleep 1
done

if [ "$BACKEND_OK" = false ]; then
    echo -e "${RED}   ❌ Le backend n'a pas démarré${NC}"
    exit 1
fi
echo -e "${GREEN}   ✓ Backend OK${NC}"

echo -e "${BLUE}   → Démarrage du frontend...${NC}"
cd frontend
npm run dev 2>&1 | sed 's/^/   [FRONTEND] /' &
FRONTEND_PID=$!
cd ..

sleep 4
echo -e "${GREEN}   ✓ Frontend OK${NC}"

echo "$BACKEND_PID" > .autocut.pid
echo "$FRONTEND_PID" >> .autocut.pid

echo ""
sleep 1

if command -v open &> /dev/null; then
    open http://localhost:5173
fi

echo -e "${CYAN}"
echo "╔════════════════════════════════════════╗"
echo "║     ✅  AutoCut est actif !            ║"
echo "╚════════════════════════════════════════╝"
echo -e "${NC}"
echo ""
echo -e "${GREEN}🎯 URLs :${NC}"
echo "   • Backend  : http://localhost:8765"
echo "   • Frontend : http://localhost:5173"
echo ""
echo -e "${YELLOW}📊 Logs en temps réel ci-dessous${NC}"
echo -e "${RED}🛑 Appuyez sur ENTRÉE pour arrêter${NC}"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

read -p ""