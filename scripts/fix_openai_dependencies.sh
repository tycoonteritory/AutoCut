#!/bin/bash

echo "========================================="
echo "  Fixing OpenAI Dependencies"
echo "========================================="
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Activate venv
source backend/venv/bin/activate

echo "[1/3] Uninstalling conflicting packages..."
pip uninstall -y tiktoken openai openai-whisper

echo ""
echo "[2/3] Reinstalling OpenAI packages in correct order..."
pip install tiktoken==0.7.0
pip install openai==1.54.0
pip install openai-whisper==20231117

echo ""
echo "[3/3] Verifying installation..."
python -c "from openai import OpenAI; print('OpenAI client: OK')"
python -c "import whisper; print('Whisper: OK')"
python -c "import tiktoken; print('Tiktoken: OK')"

echo ""
echo "========================================="
echo "  Dependencies fixed!"
echo "========================================="
echo ""
echo "Now restart the backend server."
