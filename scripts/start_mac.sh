#!/bin/bash

echo "========================================"
echo "    AutoCut - Automatic Video Cutter"
echo "========================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration des ports
BACKEND_PORT=8765
FRONTEND_PORT=5173

# Fonction pour libérer un port
free_port() {
    local port=$1
    local port_name=$2

    echo -e "${YELLOW}Vérification du port $port ($port_name)...${NC}"

    if command -v lsof &> /dev/null; then
        local pids=$(lsof -ti:$port 2>/dev/null)
        if [ ! -z "$pids" ]; then
            echo -e "${RED}Port $port occupé - libération automatique...${NC}"
            echo "$pids" | xargs kill -9 2>/dev/null
            sleep 1
            echo -e "${GREEN}Port $port libéré${NC}"
        else
            echo -e "${GREEN}Port $port disponible${NC}"
        fi
    elif command -v netstat &> /dev/null; then
        local pid=$(netstat -tlnp 2>/dev/null | grep ":$port " | awk '{print $7}' | cut -d'/' -f1)
        if [ ! -z "$pid" ]; then
            echo -e "${RED}Port $port occupé - libération automatique...${NC}"
            kill -9 $pid 2>/dev/null
            sleep 1
            echo -e "${GREEN}Port $port libéré${NC}"
        else
            echo -e "${GREEN}Port $port disponible${NC}"
        fi
    fi
}

# Check for Python - prefer 3.12, then 3.11, then 3.10, then 3.9, then default
PYTHON_CMD=""
if command -v python3.12 &> /dev/null; then
    PYTHON_CMD="python3.12"
    echo -e "${GREEN}[OK] Using Python 3.12${NC}"
elif command -v python3.11 &> /dev/null; then
    PYTHON_CMD="python3.11"
    echo -e "${GREEN}[OK] Using Python 3.11${NC}"
elif command -v python3.10 &> /dev/null; then
    PYTHON_CMD="python3.10"
    echo -e "${GREEN}[OK] Using Python 3.10${NC}"
elif command -v python3.9 &> /dev/null; then
    PYTHON_CMD="python3.9"
    echo -e "${GREEN}[OK] Using Python 3.9${NC}"
elif command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    if [[ "$PYTHON_VERSION" == "3.14" ]] || [[ "$PYTHON_VERSION" == "3.13" ]]; then
        echo -e "${YELLOW}[WARNING] Python $PYTHON_VERSION detected - this may cause compatibility issues${NC}"
        echo "Installing Python 3.12 is recommended:"
        echo "  brew install python@3.12"
        echo ""
        echo "Press Enter to continue anyway, or Ctrl+C to cancel..."
        read
    fi
    PYTHON_CMD="python3"
    echo -e "${GREEN}[OK] Using Python $(python3 --version)${NC}"
else
    echo -e "${RED}[ERROR] Python 3 is not installed!${NC}"
    echo "Please install Python 3.12 with Homebrew:"
    echo "  brew install python@3.12"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${RED}[ERROR] Node.js is not installed!${NC}"
    echo "Please install Node.js from https://nodejs.org/"
    echo "Or use Homebrew: brew install node"
    exit 1
fi

# Check if FFmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    echo -e "${RED}[ERROR] FFmpeg is not installed!${NC}"
    echo "Please install FFmpeg from https://ffmpeg.org/"
    echo "Or use Homebrew: brew install ffmpeg"
    exit 1
fi

echo -e "${GREEN}[OK] All dependencies are installed!${NC}"
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Install Python dependencies
echo "[1/4] Installing Python dependencies..."
if [ ! -d "backend/venv" ]; then
    echo "Creating virtual environment with $PYTHON_CMD..."
    $PYTHON_CMD -m venv backend/venv
fi

source backend/venv/bin/activate

# Upgrade pip, setuptools and wheel first (fixes Python 3.14 compatibility)
echo "Upgrading pip, setuptools and wheel..."
pip install --upgrade pip setuptools wheel > /dev/null 2>&1

echo "Installing dependencies..."
pip install -q -r backend/requirements.txt

if [ $? -ne 0 ]; then
    echo -e "${RED}[ERROR] Failed to install Python dependencies${NC}"
    echo "Trying without quiet mode to see the error..."
    pip install -r backend/requirements.txt
    exit 1
fi

echo -e "${GREEN}[OK] Python dependencies installed${NC}"
echo ""

# Install Node.js dependencies
echo "[2/4] Installing Node.js dependencies..."
cd frontend
if [ ! -d "node_modules" ]; then
    npm install
    if [ $? -ne 0 ]; then
        echo -e "${RED}[ERROR] Failed to install Node.js dependencies${NC}"
        cd ..
        exit 1
    fi
fi
cd ..
echo -e "${GREEN}[OK] Node.js dependencies installed${NC}"
echo ""

# Free ports before starting servers
echo "[3/5] Freeing ports..."
free_port $BACKEND_PORT "Backend"
free_port $FRONTEND_PORT "Frontend"
echo ""

# Start backend server
echo "[4/5] Starting backend server on port $BACKEND_PORT..."
source backend/venv/bin/activate
python -m uvicorn backend.main:app --host 127.0.0.1 --port $BACKEND_PORT > backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"

# Wait for backend to start
sleep 3

# Start frontend server
echo "[5/5] Starting frontend server on port $FRONTEND_PORT..."
cd frontend
npm run dev -- --strictPort > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..
echo "Frontend PID: $FRONTEND_PID"

echo ""
echo "========================================"
echo "  AutoCut is now running!"
echo "  "
echo "  Backend:  http://localhost:$BACKEND_PORT"
echo "  Frontend: http://localhost:$FRONTEND_PORT"
echo "  "
echo "  Opening browser in 5 seconds..."
echo "========================================"
echo ""

sleep 5

# Open browser
if command -v open &> /dev/null; then
    open http://localhost:$FRONTEND_PORT
elif command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:$FRONTEND_PORT
fi

echo ""
echo -e "${GREEN}AutoCut is running!${NC}"
echo ""
echo "Press Ctrl+C to stop all servers"
echo ""

# Save PIDs to file for cleanup
echo "$BACKEND_PID" > .autocut.pid
echo "$FRONTEND_PID" >> .autocut.pid

# Wait for Ctrl+C
trap cleanup INT

cleanup() {
    echo ""
    echo "Stopping AutoCut..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    rm -f .autocut.pid
    echo "AutoCut stopped."
    exit 0
}

# Keep script running
wait
