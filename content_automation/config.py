import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
FAL_KEY        = os.getenv("FAL_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENAI_MODEL   = "gpt-4o"

PROFILES_DIR = BASE_DIR / "profiles"
HISTORY_DIR  = BASE_DIR / "history"
ASSETS_DIR   = BASE_DIR / "assets"
OUTPUT_DIR   = BASE_DIR / "output"

INSTAGRAM_WIDTH  = 1080
INSTAGRAM_HEIGHT = 1350
