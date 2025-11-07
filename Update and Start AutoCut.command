#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

clear
echo "========================================"
echo "    🔄 AutoCut - Update & Start"
echo "========================================"
echo ""
echo -e "${CYAN}This will clean and reinstall everything${NC}"
echo ""

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
    echo "Please install Python 3 with: brew install python@3.12"
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

echo -e "${GREEN}✓ Node.js installed: $(node --version)${NC}"

# Check if FFmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    echo -e "${RED}❌ FFmpeg is not installed!${NC}"
    echo "Please install FFmpeg with: brew install ffmpeg"
    read -p "Press Enter to exit..."
    exit 1
fi

echo -e "${GREEN}✓ FFmpeg installed${NC}"
echo ""

# Stop any running instances
if [ -f ".autocut.pid" ]; then
    echo -e "${YELLOW}🛑 Stopping any running instances...${NC}"
    BACKEND_PID=$(head -n 1 .autocut.pid)
    FRONTEND_PID=$(tail -n 1 .autocut.pid)

    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        kill $BACKEND_PID 2>/dev/null
        echo "  Stopped backend (PID: $BACKEND_PID)"
    fi

    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        kill $FRONTEND_PID 2>/dev/null
        echo "  Stopped frontend (PID: $FRONTEND_PID)"
    fi

    rm .autocut.pid
    sleep 2
    echo ""
fi

# Clean old virtual environment
if [ -d "backend/venv" ]; then
    echo -e "${YELLOW}🧹 Removing old virtual environment...${NC}"
    rm -rf backend/venv
    echo -e "${GREEN}✓ Old venv removed${NC}"
    echo ""
fi

# Create new virtual environment
echo -e "${BLUE}📦 Creating fresh virtual environment...${NC}"
$PYTHON_CMD -m venv backend/venv

if [ ! -d "backend/venv" ]; then
    echo -e "${RED}❌ Failed to create virtual environment${NC}"
    read -p "Press Enter to exit..."
    exit 1
fi

echo -e "${GREEN}✓ Virtual environment created${NC}"
echo ""

# Activate virtual environment
source backend/venv/bin/activate

# Upgrade pip
echo -e "${BLUE}📦 Upgrading pip...${NC}"
pip install --upgrade pip setuptools wheel > /dev/null 2>&1
echo -e "${GREEN}✓ pip upgraded${NC}"
echo ""

# Install Python dependencies
echo -e "${BLUE}📦 Installing Python dependencies...${NC}"
echo "   (This may take 2-3 minutes for all packages)"
echo ""

pip install -r backend/requirements.txt

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ All Python dependencies installed successfully!${NC}"
else
    echo ""
    echo -e "${RED}❌ Failed to install Python dependencies${NC}"
    echo "Check the error messages above"
    read -p "Press Enter to exit..."
    exit 1
fi
echo ""

# Install Node.js dependencies if needed
if [ ! -d "frontend/node_modules" ]; then
    echo -e "${BLUE}📦 Installing Node.js dependencies...${NC}"
    cd frontend
    npm install
    cd ..
    echo -e "${GREEN}✓ Node.js dependencies installed${NC}"
    echo ""
else
    echo -e "${GREEN}✓ Node.js dependencies already installed${NC}"
    echo ""
fi

# Initialize database
echo -e "${BLUE}💾 Initializing database...${NC}"
source backend/venv/bin/activate
python -c "from backend.database import init_db; init_db(); print('✓ Database initialized')" 2>/dev/null
echo ""

# Start backend server
echo -e "${BLUE}🚀 Starting backend server...${NC}"
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8765 > backend.log 2>&1 &
BACKEND_PID=$!
echo "   Backend PID: $BACKEND_PID"

# Wait for backend to start
sleep 3

# Check if backend is running
if ps -p $BACKEND_PID > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend started successfully${NC}"
else
    echo -e "${RED}❌ Backend failed to start${NC}"
    echo "Check backend.log for errors"
    read -p "Press Enter to exit..."
    exit 1
fi
echo ""

# Start frontend server
echo -e "${BLUE}🚀 Starting frontend server...${NC}"
cd frontend
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..
echo "   Frontend PID: $FRONTEND_PID"

# Save PIDs
echo "$BACKEND_PID" > .autocut.pid
echo "$FRONTEND_PID" >> .autocut.pid

# Wait for frontend to start
sleep 3

# Check if frontend is running
if ps -p $FRONTEND_PID > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Frontend started successfully${NC}"
else
    echo -e "${RED}❌ Frontend failed to start${NC}"
    echo "Check frontend.log for errors"
    read -p "Press Enter to exit..."
    exit 1
fi
echo ""

echo "========================================"
echo -e "  ${GREEN}✅ AutoCut is now running!${NC}"
echo "  "
echo "  Backend:  http://localhost:8765"
echo "  Frontend: http://localhost:5173"
echo "  "
echo -e "  ${CYAN}New Features (v2.0.0):${NC}"
echo "  🎤 Filler words detection"
echo "  🔊 Audio enhancement"
echo "  📜 Job history"
echo "  💾 Database persistence"
echo "========================================"
echo ""

# Open browser
if command -v open &> /dev/null; then
    echo "🌐 Opening browser..."
    sleep 2
    open http://localhost:5173
fi

echo ""
echo -e "${GREEN}🎉 Setup complete!${NC}"
echo ""
echo "To stop AutoCut, double-click 'Stop AutoCut.command'"
echo ""
echo "Logs are saved in:"
echo "  - backend.log"
echo "  - frontend.log"
echo ""
read -p "Press Enter to close this window (AutoCut will keep running)..."
