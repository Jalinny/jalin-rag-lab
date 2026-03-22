from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
CHROMA_PATH: str = os.getenv("CHROMA_PATH", "chroma_db")
DATA_PATH: str = os.getenv("DATA_PATH", "data")
VOYAGE_API_KEY: str = os.getenv("VOYAGE_API_KEY", "")
EMBED_MODEL: str = "voyage-3"
CLAUDE_MODEL: str = "claude-sonnet-4-6"
CHUNK_SIZE: int = 1000
CHUNK_OVERLAP: int = 200
RETRIEVAL_K: int = 15
