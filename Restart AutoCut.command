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
echo "    🔄 AutoCut - Restarting..."
echo "========================================"
echo ""

# Check if PID file exists
if [ ! -f ".autocut.pid" ]; then
    echo -e "${YELLOW}⚠️  AutoCut is not running${NC}"
    echo "Starting AutoCut instead..."
    echo ""

    # Just start it
    bash "$SCRIPT_DIR/Start AutoCut.command"
    exit 0
fi

# Read PIDs
BACKEND_PID=$(head -n 1 .autocut.pid)
FRONTEND_PID=$(tail -n 1 .autocut.pid)

echo "🛑 Stopping current instance..."
echo ""

# Stop backend
if ps -p $BACKEND_PID > /dev/null 2>&1; then
    echo "  • Stopping backend server..."
    kill $BACKEND_PID 2>/dev/null
fi

# Stop frontend
if ps -p $FRONTEND_PID > /dev/null 2>&1; then
    echo "  • Stopping frontend server..."
    kill $FRONTEND_PID 2>/dev/null
fi

# Kill any remaining processes on ports
lsof -ti:8765 2>/dev/null | xargs kill 2>/dev/null
lsof -ti:5173 2>/dev/null | xargs kill 2>/dev/null

# Remove PID file
rm -f .autocut.pid

# Wait a bit
sleep 2

echo ""
echo -e "${GREEN}✓ Stopped${NC}"
echo ""
echo "🚀 Starting AutoCut..."
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
    read -p "Press Enter to exit..."
    exit 1
fi

# Pull latest changes from git
echo "📥 Checking for updates..."
git fetch origin > /dev/null 2>&1
LOCAL=$(git rev-parse @)
REMOTE=$(git rev-parse @{u} 2>/dev/null)

if [ ! -z "$REMOTE" ] && [ "$LOCAL" != "$REMOTE" ]; then
    echo -e "${BLUE}📥 Updates available! Pulling latest changes...${NC}"
    git pull

    # Reinstall dependencies in case they changed
    echo "📦 Updating dependencies..."
    source backend/venv/bin/activate
    pip install -q -r backend/requirements.txt

    cd frontend
    npm install
    cd ..
else
    echo -e "${GREEN}✓ Already up to date${NC}"
fi

echo ""

# Start backend server
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
echo -e "  ${GREEN}✅ AutoCut restarted successfully!${NC}"
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
echo -e "${GREEN}🎉 AutoCut is ready!${NC}"
echo ""
read -p "Press Enter to close this window (AutoCut will keep running)..."
