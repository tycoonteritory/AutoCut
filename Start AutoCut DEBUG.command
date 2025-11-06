#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

echo "========================================"
echo "    🐛 AutoCut - DEBUG MODE"
echo "========================================"
echo ""

# Check if already running
if [ -f ".autocut.pid" ]; then
    BACKEND_PID=$(head -n 1 .autocut.pid)
    FRONTEND_PID=$(tail -n 1 .autocut.pid)

    if ps -p $BACKEND_PID > /dev/null 2>&1 || ps -p $FRONTEND_PID > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  AutoCut is already running!${NC}"
        echo "Please stop it first with 'Stop AutoCut.command'"
        echo ""
        read -p "Press Enter to exit..."
        exit 0
    fi
fi

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
    echo -e "${RED}❌ Python 3 is not installed!${NC}"
    read -p "Press Enter to exit..."
    exit 1
fi

echo -e "${GREEN}✓ Using Python: $PYTHON_CMD${NC}"

# Install dependencies
if [ ! -d "backend/venv" ]; then
    echo "📦 Creating virtual environment..."
    $PYTHON_CMD -m venv backend/venv
fi

source backend/venv/bin/activate

echo "📦 Installing Python dependencies..."
pip install -q --upgrade pip setuptools wheel
pip install -q -r backend/requirements.txt

if [ ! -d "frontend/node_modules" ]; then
    echo "📦 Installing Node.js dependencies..."
    cd frontend
    npm install
    cd ..
fi

echo ""
echo -e "${MAGENTA}========================================${NC}"
echo -e "${MAGENTA}   🐛 DEBUG MODE ACTIVE${NC}"
echo -e "${MAGENTA}========================================${NC}"
echo ""
echo "This will run servers in FOREGROUND with full logging"
echo "You'll see all debug output in this terminal"
echo ""
echo -e "${YELLOW}To stop: Press Ctrl+C${NC}"
echo ""
read -p "Press Enter to start..."

echo ""
echo -e "${BLUE}🚀 Starting backend in DEBUG mode...${NC}"
echo ""

# Start backend in foreground
source backend/venv/bin/activate

# Set debug environment variables
export PYTHONUNBUFFERED=1
export LOG_LEVEL=DEBUG

# Start backend in current terminal (foreground)
echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}   BACKEND DEBUG OUTPUT${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""

# Run backend with reload for auto-restart on code changes
python -m uvicorn backend.main:app \
    --host 127.0.0.1 \
    --port 8765 \
    --reload \
    --log-level debug

# This will only run when backend is stopped (Ctrl+C)
echo ""
echo -e "${YELLOW}Backend stopped${NC}"
echo ""
read -p "Press Enter to close..."
