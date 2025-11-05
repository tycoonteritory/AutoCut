#!/bin/bash
# Quick fix script for Python 3.14 compatibility issues
# This script installs Python 3.12 and recreates the virtual environment

echo "=========================================="
echo "  AutoCut - Python 3.14 Fix Script"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check current Python version
CURRENT_VERSION=$(python3 --version 2>&1)
echo "Current Python: $CURRENT_VERSION"
echo ""

# Check if Python 3.12 is already installed
if command -v python3.12 &> /dev/null; then
    echo -e "${GREEN}[OK] Python 3.12 is already installed!${NC}"
else
    echo -e "${YELLOW}[INFO] Python 3.12 not found. Installing...${NC}"

    # Check if Homebrew is installed
    if ! command -v brew &> /dev/null; then
        echo -e "${RED}[ERROR] Homebrew is not installed!${NC}"
        echo "Please install Homebrew first:"
        echo '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
        exit 1
    fi

    # Install Python 3.12
    echo "Installing Python 3.12 via Homebrew..."
    brew install python@3.12

    if [ $? -ne 0 ]; then
        echo -e "${RED}[ERROR] Failed to install Python 3.12${NC}"
        exit 1
    fi

    echo -e "${GREEN}[OK] Python 3.12 installed successfully!${NC}"
fi

echo ""
echo "Python 3.12 version: $(python3.12 --version)"
echo ""

# Remove old virtual environment
if [ -d "backend/venv" ]; then
    echo "Removing old virtual environment..."
    rm -rf backend/venv
    echo -e "${GREEN}[OK] Old venv removed${NC}"
fi

echo ""
echo "Creating new virtual environment with Python 3.12..."
python3.12 -m venv backend/venv

if [ $? -ne 0 ]; then
    echo -e "${RED}[ERROR] Failed to create virtual environment${NC}"
    exit 1
fi

echo -e "${GREEN}[OK] Virtual environment created${NC}"
echo ""

# Activate and install dependencies
echo "Installing Python dependencies..."
source backend/venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r backend/requirements.txt

if [ $? -ne 0 ]; then
    echo -e "${RED}[ERROR] Failed to install dependencies${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}=========================================="
echo "  ✅ Python 3.12 setup complete!"
echo "==========================================${NC}"
echo ""
echo "You can now run AutoCut with:"
echo "  ./scripts/start_mac.sh"
echo ""
