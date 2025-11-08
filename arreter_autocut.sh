#!/bin/bash

echo "========================================"
echo "    AutoCut - Arrêt"
echo "========================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if PID file exists
if [ ! -f ".autocut.pid" ]; then
    echo "AutoCut n'est pas en cours d'exécution (fichier PID introuvable)"
    echo ""
    exit 0
fi

echo "Arrêt des serveurs AutoCut..."
echo ""

# Kill processes from PID file
if [ -f ".autocut.pid" ]; then
    while read pid; do
        if kill $pid 2>/dev/null; then
            echo "Arrêt du processus $pid"
        fi
    done < .autocut.pid
    rm -f .autocut.pid
fi

# Fallback: kill by port (backend)
echo "Vérification des processus sur le port 8765..."
if command -v lsof &> /dev/null; then
    lsof -ti:8765 | xargs kill -9 2>/dev/null
elif command -v fuser &> /dev/null; then
    fuser -k 8765/tcp 2>/dev/null
fi

# Fallback: kill by port (frontend)
echo "Vérification des processus sur le port 5173..."
if command -v lsof &> /dev/null; then
    lsof -ti:5173 | xargs kill -9 2>/dev/null
elif command -v fuser &> /dev/null; then
    fuser -k 5173/tcp 2>/dev/null
fi

echo ""
echo "========================================"
echo "  AutoCut arrêté avec succès!"
echo "========================================"
echo ""
