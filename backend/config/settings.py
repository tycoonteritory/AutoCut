"""
Configuration settings for AutoCut application
"""
import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
TEMP_DIR = BASE_DIR / "temp"
OUTPUT_DIR = BASE_DIR / "output"

# Create directories if they don't exist
UPLOAD_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# Server configuration
API_HOST = "127.0.0.1"
API_PORT = 8765
WS_PORT = 8766

# Video processing settings
SUPPORTED_FORMATS = [".mp4", ".mov"]
MAX_FILE_SIZE = 10 * 1024 * 1024 * 1024  # 10GB

# Silence detection settings
SILENCE_THRESHOLD_DB = -40  # dB threshold for silence detection
MIN_SILENCE_DURATION_MS = 500  # Minimum silence duration in milliseconds
PADDING_MS = 100  # Padding around cuts in milliseconds

# Export settings
EXPORT_FORMATS = ["premiere_pro", "final_cut_pro"]
