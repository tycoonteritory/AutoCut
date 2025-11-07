#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "========================================"
echo "    🎬 AutoCut - Starting..."
echo "========================================"
echo ""

# Check if already running
if [ -f ".autocut.pid" ]; then
    BACKEND_PID=$(head -n 1 .autocut.pid)
    FRONTEND_PID=$(tail -n 1 .autocut.pid)

    if ps -p $BACKEND_PID > /dev/null 2>&1 || ps -p $FRONTEND_PID > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  AutoCut is already running!${NC}"
        echo ""
        echo "Backend:  http://localhost:8765"
        echo "Frontend: http://localhost:5173"
        echo ""
        echo "If you want to restart, use 'Restart AutoCut.command'"
        echo "If you want to stop, use 'Stop AutoCut.command'"
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
    echo "Please install Python 3.12 with: brew install python@3.12"
    read -p "Press Enter to exit..."
    exit 1
fi

echo -e "${GREEN}✓ Using Python: $PYTHON_CMD${NC}"

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js is not installed!${NC}"
    echo "Please install Node.js from https://nodejs.org/"
    read -p "Press Enter to exit..."
    exit 1
fi

echo -e "${GREEN}✓ Node.js installed${NC}"

# Check if FFmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    echo -e "${RED}❌ FFmpeg is not installed!${NC}"
    echo "Please install FFmpeg with: brew install ffmpeg"
    read -p "Press Enter to exit..."
    exit 1
fi

echo -e "${GREEN}✓ FFmpeg installed${NC}"
echo ""

# Install Python dependencies if needed
if [ ! -d "backend/venv" ]; then
    echo "📦 Creating virtual environment..."
    $PYTHON_CMD -m venv backend/venv
fi

source backend/venv/bin/activate

# Check if new dependencies are installed
echo "🔍 Checking dependencies..."
NEED_INSTALL=false

# Check for new v2.0.0 dependencies
python -c "import sqlalchemy" 2>/dev/null || NEED_INSTALL=true
python -c "import noisereduce" 2>/dev/null || NEED_INSTALL=true
python -c "import librosa" 2>/dev/null || NEED_INSTALL=true

if [ "$NEED_INSTALL" = true ]; then
    echo ""
    echo -e "${YELLOW}⚠️  New dependencies detected (v2.0.0)${NC}"
    echo "📦 Installing updated dependencies..."
    echo "   (This may take 2-3 minutes)"
    echo ""
    pip install -q --upgrade pip setuptools wheel
    pip install -r backend/requirements.txt
    echo ""
    echo -e "${GREEN}✓ Dependencies updated successfully!${NC}"
    echo ""
else
    echo -e "${GREEN}✓ All dependencies up to date${NC}"
fi

# Install Node.js dependencies if needed
if [ ! -d "frontend/node_modules" ]; then
    echo "📦 Installing Node.js dependencies..."
    cd frontend
    npm install
    cd ..
fi

# Start backend server
echo ""
echo -e "${BLUE}🚀 Starting backend server...${NC}"
source backend/venv/bin/activate
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8765 > backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"

# Wait for backend to start
sleep 3

# Start frontend server
echo -e "${BLUE}🚀 Starting frontend server...${NC}"
cd frontend
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..
echo "Frontend PID: $FRONTEND_PID"

# Save PIDs
echo "$BACKEND_PID" > .autocut.pid
echo "$FRONTEND_PID" >> .autocut.pid

# Wait a bit
sleep 3

echo ""
echo "========================================"
echo -e "  ${GREEN}✅ AutoCut is now running!${NC}"
echo "  "
echo "  Backend:  http://localhost:8765"
echo "  Frontend: http://localhost:5173"
echo "  "
echo "  Opening browser..."
echo "========================================"
echo ""

# Open browser
if command -v open &> /dev/null; then
    open http://localhost:5173
fi

echo ""
echo -e "${GREEN}🎉 AutoCut started successfully!${NC}"
echo ""
echo "To stop AutoCut, double-click 'Stop AutoCut.command'"
echo "To restart AutoCut, double-click 'Restart AutoCut.command'"
echo ""
echo "Logs are saved in:"
echo "  - backend.log"
echo "  - frontend.log"
echo ""
read -p "Press Enter to close this window (AutoCut will keep running)..."
