import os

from dotenv import load_dotenv

load_dotenv()  
# Load environment variables from .env file
# Without this .env sits unused 


BACKEND_API_URL = os.getenv("BACKEND_API_URL")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")