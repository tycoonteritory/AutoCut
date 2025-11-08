#!/bin/bash

echo "========================================"
echo "    AutoCut - Démarrage Backend Seul"
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

# Check for Python
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
    echo -e "${RED}[ERREUR] Python 3 n'est pas installé!${NC}"
    exit 1
fi

echo -e "${GREEN}[OK] Python trouvé: $($PYTHON_CMD --version)${NC}"

# Create venv if needed
if [ ! -d "backend/venv" ]; then
    echo "Création de l'environnement virtuel..."
    $PYTHON_CMD -m venv backend/venv
    if [ $? -ne 0 ]; then
        echo -e "${RED}[ERREUR] Échec de la création de l'environnement virtuel${NC}"
        exit 1
    fi
fi

# Activate virtual environment
source backend/venv/bin/activate

# Function to check if Python package is installed
check_python_package() {
    python -c "import $1" 2>/dev/null
    return $?
}

# Check critical Python dependencies
PYTHON_DEPS_MISSING=false
echo "Vérification des dépendances Python critiques..."

if ! check_python_package "fastapi"; then
    echo -e "${YELLOW}[!] FastAPI non installé${NC}"
    PYTHON_DEPS_MISSING=true
elif ! check_python_package "uvicorn"; then
    echo -e "${YELLOW}[!] Uvicorn non installé${NC}"
    PYTHON_DEPS_MISSING=true
elif ! check_python_package "sqlalchemy"; then
    echo -e "${YELLOW}[!] SQLAlchemy non installé${NC}"
    PYTHON_DEPS_MISSING=true
else
    echo -e "${GREEN}[OK] Dépendances Python principales présentes${NC}"
fi

# Install Python dependencies if needed
if [ "$PYTHON_DEPS_MISSING" = true ]; then
    echo ""
    echo -e "${YELLOW}Installation des dépendances Python manquantes...${NC}"
    echo "Cela peut prendre plusieurs minutes (PyTorch + CUDA = ~5GB)"
    echo ""

    pip install --upgrade pip setuptools wheel -q
    pip install -r backend/requirements.txt

    if [ $? -ne 0 ]; then
        echo -e "${RED}[ERREUR] Échec de l'installation des dépendances Python${NC}"
        exit 1
    fi
    echo -e "${GREEN}[OK] Dépendances Python installées avec succès${NC}"
else
    echo -e "${BLUE}[INFO] Dépendances Python déjà installées${NC}"
fi

echo ""
echo "========================================"
echo "    Démarrage du serveur backend"
echo "========================================"
echo ""
echo "Backend API sera disponible sur: http://localhost:8765"
echo "Documentation API: http://localhost:8765/docs"
echo ""
echo "Pour arrêter: Appuyez sur Ctrl+C"
echo ""

# Set environment variables
export PYTHONUNBUFFERED=1
export LOG_LEVEL=INFO

# Start backend
echo -e "${GREEN}Démarrage...${NC}"
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8765 --reload
