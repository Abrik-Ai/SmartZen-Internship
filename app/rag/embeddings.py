from functools import lru_cache

from langchain_ollama import OllamaEmbeddings

from app.config import OLLAMA_BASE_URL, OLLAMA_EMBED_MODEL

EMBEDDING_DIMENSION = 768


@lru_cache
def get_embedding_model() -> OllamaEmbeddings:
    return OllamaEmbeddings(model=OLLAMA_EMBED_MODEL, base_url=OLLAMA_BASE_URL)


def embed_text(text: str) -> list[float]:
    try:
        return get_embedding_model().embed_query(text)
    except Exception as exc:
        raise RuntimeError(
            "Failed to generate embedding using Ollama."
        ) from exc
