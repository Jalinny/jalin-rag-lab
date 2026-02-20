from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

ANTHROPIC_API_KEY: str = os.environ["ANTHROPIC_API_KEY"]
CHROMA_PATH: str = os.getenv("CHROMA_PATH", "chroma_db")
DATA_PATH: str = os.getenv("DATA_PATH", "data")
EMBED_MODEL: str = "all-MiniLM-L6-v2"
CLAUDE_MODEL: str = "claude-sonnet-4-6"
CHUNK_SIZE: int = 1000
CHUNK_OVERLAP: int = 200
RETRIEVAL_K: int = 15
