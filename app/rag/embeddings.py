from functools import lru_cache

from langchain_ollama import OllamaEmbeddings

MODEL_NAME = "nomic-embed-text"
EMBEDDING_DIMENSION = 768  # nomic-embed-text outputs 768-dimensional vectors


@lru_cache
def get_embedding_model() -> OllamaEmbeddings:
    """
    Create and cache the Ollama embedding model.

    The model is initialized only once and reused for future requests.
    """
    return OllamaEmbeddings(model=MODEL_NAME)


def embed_text(text: str) -> list[float]:
    """
    Generate an embedding for the given text.

    TEMPORARY:
    A mock embedding is returned because Ollama is unstable on this
    development machine. The real implementation is kept below and can
    be restored by uncommenting it.
    """

    # -----------------------------
    # TEMPORARY MOCK IMPLEMENTATION
    # -----------------------------
    # Return a deterministic dummy vector with the correct dimension.
    # This allows the ingestion pipeline and database logic to be
    # developed and tested without a working Ollama runtime.
    return [0.0] * EMBEDDING_DIMENSION

    # -----------------------------
    # REAL IMPLEMENTATION
    # -----------------------------
    # try:
    #     return get_embedding_model().embed_query(text)
    # except Exception as exc:
    #     raise RuntimeError(
    #         "Failed to generate embedding using Ollama."
    #     ) from exc