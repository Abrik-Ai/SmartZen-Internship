import os

from dotenv import load_dotenv

load_dotenv()  
# Load environment variables from .env file
# Without this .env sits unused 


BACKEND_API_URL = os.getenv("BACKEND_API_URL")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
JWT_ACCESS_SECRET = os.getenv("JWT_ACCESS_SECRET")
if not JWT_ACCESS_SECRET:
    raise ValueError("JWT_ACCESS_SECRET is not set")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
