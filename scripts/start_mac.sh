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

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[ERROR] Python 3 is not installed!${NC}"
    echo "Please install Python 3.8 or higher from https://www.python.org/"
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
    echo "Creating virtual environment..."
    python3 -m venv backend/venv
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

# Start backend server
echo "[3/4] Starting backend server on port 8765..."
source backend/venv/bin/activate
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8765 > backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"

# Wait for backend to start
sleep 3

# Start frontend server
echo "[4/4] Starting frontend server on port 5173..."
cd frontend
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..
echo "Frontend PID: $FRONTEND_PID"

echo ""
echo "========================================"
echo "  AutoCut is now running!"
echo "  "
echo "  Backend:  http://localhost:8765"
echo "  Frontend: http://localhost:5173"
echo "  "
echo "  Opening browser in 5 seconds..."
echo "========================================"
echo ""

sleep 5

# Open browser
if command -v open &> /dev/null; then
    open http://localhost:5173
elif command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:5173
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
