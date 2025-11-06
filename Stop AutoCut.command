#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================"
echo "    🛑 AutoCut - Stopping..."
echo "========================================"
echo ""

# Check if PID file exists
if [ ! -f ".autocut.pid" ]; then
    echo -e "${YELLOW}⚠️  AutoCut is not running (no PID file found)${NC}"
    echo ""
    read -p "Press Enter to exit..."
    exit 0
fi

# Read PIDs
BACKEND_PID=$(head -n 1 .autocut.pid)
FRONTEND_PID=$(tail -n 1 .autocut.pid)

STOPPED_SOMETHING=false

# Stop backend
if ps -p $BACKEND_PID > /dev/null 2>&1; then
    echo "🛑 Stopping backend server (PID: $BACKEND_PID)..."
    kill $BACKEND_PID 2>/dev/null
    STOPPED_SOMETHING=true
else
    echo "ℹ️  Backend server is not running"
fi

# Stop frontend
if ps -p $FRONTEND_PID > /dev/null 2>&1; then
    echo "🛑 Stopping frontend server (PID: $FRONTEND_PID)..."
    kill $FRONTEND_PID 2>/dev/null
    STOPPED_SOMETHING=true
else
    echo "ℹ️  Frontend server is not running"
fi

# Also try to kill any remaining processes
echo ""
echo "🔍 Checking for any remaining AutoCut processes..."

# Kill any uvicorn processes running on port 8765
UVICORN_PIDS=$(lsof -ti:8765 2>/dev/null)
if [ ! -z "$UVICORN_PIDS" ]; then
    echo "🛑 Stopping backend processes on port 8765..."
    echo $UVICORN_PIDS | xargs kill 2>/dev/null
    STOPPED_SOMETHING=true
fi

# Kill any vite/npm processes running on port 5173
VITE_PIDS=$(lsof -ti:5173 2>/dev/null)
if [ ! -z "$VITE_PIDS" ]; then
    echo "🛑 Stopping frontend processes on port 5173..."
    echo $VITE_PIDS | xargs kill 2>/dev/null
    STOPPED_SOMETHING=true
fi

# Remove PID file
rm -f .autocut.pid

echo ""
if [ "$STOPPED_SOMETHING" = true ]; then
    echo "========================================"
    echo -e "  ${GREEN}✅ AutoCut stopped successfully!${NC}"
    echo "========================================"
else
    echo "========================================"
    echo -e "  ${YELLOW}ℹ️  AutoCut was not running${NC}"
    echo "========================================"
fi
echo ""
read -p "Press Enter to close this window..."
