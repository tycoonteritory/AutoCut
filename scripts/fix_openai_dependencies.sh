#!/bin/bash

echo "========================================="
echo "  🔧 Fixing OpenAI Dependencies"
echo "========================================="
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Activate venv
source backend/venv/bin/activate

echo "[1/4] Uninstalling all OpenAI-related packages..."
pip uninstall -y tiktoken openai openai-whisper 2>/dev/null

# Clean pip cache to avoid conflicts
echo ""
echo "[2/4] Cleaning pip cache..."
pip cache purge 2>/dev/null

echo ""
echo "[3/4] Reinstalling OpenAI packages in correct order..."
echo "  → Installing tiktoken 0.7.0 first..."
pip install --no-cache-dir tiktoken==0.7.0

echo "  → Installing openai 1.54.0..."
pip install --no-cache-dir openai==1.54.0

echo "  → Installing openai-whisper..."
pip install --no-cache-dir openai-whisper==20231117

echo ""
echo "[4/4] Verifying installation..."
python -c "from openai import OpenAI; client = OpenAI(api_key='test'); print('✓ OpenAI client: OK')" || echo "✗ OpenAI failed"
python -c "import whisper; print('✓ Whisper: OK')" || echo "✗ Whisper failed"
python -c "import tiktoken; print('✓ Tiktoken: OK')" || echo "✗ Tiktoken failed"

echo ""
echo "========================================="
echo "  ✅ Dependencies fixed!"
echo "========================================="
echo ""
echo "Now restart the backend server."
echo ""
