"""
Configuration settings for AutoCut application
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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

# Silence detection settings (Phase 1)
SILENCE_THRESHOLD_DB = int(os.getenv("SILENCE_THRESHOLD_DB", -40))
MIN_SILENCE_DURATION_MS = int(os.getenv("MIN_SILENCE_DURATION_MS", 500))
PADDING_MS = int(os.getenv("PADDING_MS", 100))

# Export settings
EXPORT_FORMATS = ["premiere_pro", "final_cut_pro"]

# Phase 2 - OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
if not OPENAI_API_KEY:
    print("⚠️  WARNING: OPENAI_API_KEY not set. Phase 2 features (transcription, YouTube optimization) will not work.")
    print("   Create a .env file with your OpenAI API key. See .env.example for details.")

# Phase 2 - Transcription settings
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")  # tiny, base, small, medium, large
TRANSCRIPTION_LANGUAGE = os.getenv("TRANSCRIPTION_LANGUAGE", "fr")  # French by default

# Phase 2 - YouTube Optimization settings
GPT_MODEL = os.getenv("GPT_MODEL", "gpt-4")
NUM_TITLE_SUGGESTIONS = 3
NUM_THUMBNAIL_SUGGESTIONS = 5
MAX_TAGS = 10
