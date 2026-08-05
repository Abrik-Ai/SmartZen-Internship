import ollama

from app.config import OLLAMA_BASE_URL, OLLAMA_MODEL


def check_ollama_status() -> bool:
    if not OLLAMA_BASE_URL:
        return False
    try:
        response = ollama.Client(host=OLLAMA_BASE_URL).list()
    except ConnectionError:
        return False

    model_names = [m.model for m in response.models]
    return OLLAMA_MODEL in model_names
