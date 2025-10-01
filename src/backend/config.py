import os
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# 🔑 OpenAI API key - MUST be set as environment variable
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError(
        "OPENAI_API_KEY environment variable is not set. "
        "Please set it before running the application.\n"
        "Example: export OPENAI_API_KEY='your-key-here'\n"
        "Or create a .env file with: OPENAI_API_KEY=your-key-here"
    )

# ✅ Shared OpenAI client
OPENAI_CLIENT = OpenAI(api_key=OPENAI_API_KEY)

# Rest of your config stays the same...
HOME_DIR = Path.home()
APP_DIR = HOME_DIR / "Library" / "Application Support" / "FileChat"
DB_DIR = APP_DIR / "database"
CACHE_DIR = APP_DIR / "cache"

DB_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)

CHROMA_PERSIST_DIR = str(DB_DIR)
COLLECTION_NAME = "filechat_docs"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50