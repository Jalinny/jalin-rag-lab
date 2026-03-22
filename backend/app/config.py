from dotenv import load_dotenv
import os

load_dotenv()

# Anchor paths to backend/ regardless of cwd
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
CHROMA_PATH: str = os.getenv("CHROMA_PATH", os.path.join(_BACKEND_DIR, "chroma_db"))
DATA_PATH: str = os.getenv("DATA_PATH", os.path.join(_BACKEND_DIR, "data"))
CLAUDE_MODEL: str = "claude-sonnet-4-6"
CHUNK_SIZE: int = 1000
CHUNK_OVERLAP: int = 200
RETRIEVAL_K: int = 15
