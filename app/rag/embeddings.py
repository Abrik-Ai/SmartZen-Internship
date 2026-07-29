import hashlib
import random
from functools import lru_cache

from langchain_ollama import OllamaEmbeddings

MODEL_NAME = "nomic-embed-text"
EMBEDDING_DIMENSION = 768


@lru_cache
def get_embedding_model() -> OllamaEmbeddings:
    return OllamaEmbeddings(model=MODEL_NAME)


def embed_text(text: str) -> list[float]:
    """
    Temporary deterministic embedding.
    Replace with Ollama once it works.
    """

    seed = int(hashlib.sha256(text.encode("utf-8")).hexdigest(), 16)

    rng = random.Random(seed)

    return [
        rng.uniform(-1.0, 1.0)
        for _ in range(EMBEDDING_DIMENSION)
    ]

    # REAL IMPLEMENTATION
    # try:
    #     return get_embedding_model().embed_query(text)
    # except Exception as exc:
    #     raise RuntimeError(
    #         "Failed to generate embedding using Ollama."
    #     ) from exc