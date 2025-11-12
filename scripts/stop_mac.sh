#!/bin/bash

echo "Stopping AutoCut..."

# Configuration des ports
BACKEND_PORT=8765
FRONTEND_PORT=5173

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

if [ -f ".autocut.pid" ]; then
    while read pid; do
        kill $pid 2>/dev/null
        echo "Stopped process $pid"
    done < .autocut.pid
    rm -f .autocut.pid
fi

# Fallback: kill by port
echo "Cleaning up ports..."
lsof -ti:$BACKEND_PORT | xargs kill -9 2>/dev/null
lsof -ti:$FRONTEND_PORT | xargs kill -9 2>/dev/null

echo "AutoCut stopped."
