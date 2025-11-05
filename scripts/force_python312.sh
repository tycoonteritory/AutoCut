#!/bin/bash
# Force install script using Python 3.12 absolute path

echo "=========================================="
echo "  AutoCut - Force Python 3.12 Setup"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Find Python 3.12 absolute path
PYTHON312_PATH=""

# Check common Homebrew locations
if [ -f "/opt/homebrew/bin/python3.12" ]; then
    PYTHON312_PATH="/opt/homebrew/bin/python3.12"
elif [ -f "/usr/local/bin/python3.12" ]; then
    PYTHON312_PATH="/usr/local/bin/python3.12"
elif [ -f "/opt/homebrew/opt/python@3.12/bin/python3.12" ]; then
    PYTHON312_PATH="/opt/homebrew/opt/python@3.12/bin/python3.12"
elif command -v python3.12 &> /dev/null; then
    PYTHON312_PATH=$(which python3.12)
fi

if [ -z "$PYTHON312_PATH" ]; then
    echo -e "${RED}[ERROR] Python 3.12 not found!${NC}"
    echo ""
    echo "Installing Python 3.12 via Homebrew..."

    if ! command -v brew &> /dev/null; then
        echo -e "${RED}Homebrew not installed!${NC}"
        echo "Install it with:"
        echo '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
        exit 1
    fi

    brew install python@3.12

    # Try to find it again
    if [ -f "/opt/homebrew/bin/python3.12" ]; then
        PYTHON312_PATH="/opt/homebrew/bin/python3.12"
    elif [ -f "/usr/local/bin/python3.12" ]; then
        PYTHON312_PATH="/usr/local/bin/python3.12"
    elif [ -f "/opt/homebrew/opt/python@3.12/bin/python3.12" ]; then
        PYTHON312_PATH="/opt/homebrew/opt/python@3.12/bin/python3.12"
    else
        echo -e "${RED}Failed to install Python 3.12${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}[OK] Found Python 3.12: $PYTHON312_PATH${NC}"
$PYTHON312_PATH --version
echo ""

# Go to project directory
cd "$(dirname "$0")/.."
PROJECT_DIR=$(pwd)
echo "Project directory: $PROJECT_DIR"
echo ""

# Remove old venv
if [ -d "backend/venv" ]; then
    echo "Removing old virtual environment..."
    rm -rf backend/venv
    echo -e "${GREEN}[OK] Old venv removed${NC}"
fi

# Create new venv with Python 3.12 (using absolute path)
echo "Creating virtual environment with Python 3.12..."
$PYTHON312_PATH -m venv backend/venv

if [ $? -ne 0 ]; then
    echo -e "${RED}[ERROR] Failed to create venv${NC}"
    exit 1
fi

echo -e "${GREEN}[OK] Virtual environment created${NC}"
echo ""

# Activate venv
source backend/venv/bin/activate

# Verify Python version in venv
echo "Verifying Python version in venv..."
VENV_PYTHON_VERSION=$(python --version 2>&1)
echo "venv Python: $VENV_PYTHON_VERSION"

if [[ ! "$VENV_PYTHON_VERSION" =~ "3.12" ]]; then
    echo -e "${RED}[ERROR] venv is not using Python 3.12!${NC}"
    echo "Something went wrong. The venv should use Python 3.12 but uses: $VENV_PYTHON_VERSION"
    exit 1
fi

echo -e "${GREEN}[OK] venv is using Python 3.12${NC}"
echo ""

# Upgrade pip, setuptools, wheel
echo "Upgrading pip, setuptools, wheel..."
python -m pip install --upgrade pip setuptools wheel

if [ $? -ne 0 ]; then
    echo -e "${RED}[ERROR] Failed to upgrade pip/setuptools/wheel${NC}"
    exit 1
fi

echo -e "${GREEN}[OK] pip/setuptools/wheel upgraded${NC}"
echo ""

# Install dependencies
echo "Installing dependencies from requirements.txt..."
pip install -r backend/requirements.txt

if [ $? -ne 0 ]; then
    echo -e "${RED}[ERROR] Failed to install dependencies${NC}"
    exit 1
fi

echo -e "${GREEN}[OK] All dependencies installed${NC}"
echo ""

# Verify uvicorn
if python -c "import uvicorn" 2>/dev/null; then
    echo -e "${GREEN}[OK] uvicorn is installed${NC}"
else
    echo -e "${RED}[ERROR] uvicorn not installed${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}=========================================="
echo "  ✅ Setup Complete!"
echo "=========================================="
echo ""
echo "To start the backend:"
echo "  cd $PROJECT_DIR"
echo "  source backend/venv/bin/activate"
echo "  python -m uvicorn backend.main:app --host 127.0.0.1 --port 8765 --reload"
echo ""
echo "Or run the full app:"
echo "  ./scripts/start_mac.sh"
echo "${NC}"
