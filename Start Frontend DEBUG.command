#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================"
echo "    🐛 AutoCut Frontend - DEBUG MODE"
echo "========================================"
echo ""

# Check for Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed!"
    read -p "Press Enter to exit..."
    exit 1
fi

echo -e "${GREEN}✓ Node.js found${NC}"
node --version
echo ""

# Install dependencies if needed
if [ ! -d "frontend/node_modules" ]; then
    echo "📦 Installing Node.js dependencies..."
    cd frontend
    npm install
    cd ..
fi

echo -e "${MAGENTA}========================================${NC}"
echo -e "${MAGENTA}   🐛 FRONTEND DEBUG MODE ACTIVE${NC}"
echo -e "${MAGENTA}========================================${NC}"
echo ""
echo "This will run the frontend with full debug output"
echo ""
echo -e "${YELLOW}Make sure the backend is running!${NC}"
echo ""
echo -e "${YELLOW}To stop: Press Ctrl+C${NC}"
echo ""
read -p "Press Enter to start..."

echo ""
echo -e "${BLUE}🚀 Starting frontend in DEBUG mode...${NC}"
echo ""

# Start frontend in foreground
cd frontend

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}   FRONTEND DEBUG OUTPUT${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""

# Run in dev mode (foreground)
npm run dev

# This will only run when frontend is stopped
echo ""
echo "Frontend stopped"
read -p "Press Enter to close..."
