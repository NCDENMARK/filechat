import os
from pathlib import Path
from openai import OpenAI

# 🔑 OpenAI API key - MUST be set as environment variable
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError(
        "OPENAI_API_KEY environment variable is not set. "
        "Please set it before running the application.\n"
        "Example: export OPENAI_API_KEY='your-key-here'"
    )

# ✅ Shared OpenAI client
OPENAI_CLIENT = OpenAI(api_key=OPENAI_API_KEY)

# 📂 Define where to store data on the user's computer
HOME_DIR = Path.home()  # e.g. /Users/username
APP_DIR = HOME_DIR / "Library" / "Application Support" / "FileChat"
DB_DIR = APP_DIR / "database"
CACHE_DIR = APP_DIR / "cache"

# Make sure folders exist
DB_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# ⚙️ ChromaDB configuration
CHROMA_PERSIST_DIR = str(DB_DIR)
COLLECTION_NAME = "filechat_docs"

# 📝 Text processing settings
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50