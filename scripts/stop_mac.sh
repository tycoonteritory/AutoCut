#!/bin/bash

echo "Stopping AutoCut..."

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
lsof -ti:8765 | xargs kill -9 2>/dev/null
lsof -ti:5173 | xargs kill -9 2>/dev/null

echo "AutoCut stopped."
