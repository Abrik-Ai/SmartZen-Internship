from typing import TypedDict

import psycopg

from app.document_search_errors import (
    DocumentSearchConnectionError,
    DocumentSearchQueryError,
)
from app.rag.database import get_connection
from app.rag.embeddings import embed_text


class SearchResult(TypedDict):
    content: str
    source: str
    score: float


def search_docs(query: str, top_k: int = 3) -> list[SearchResult]:
    """
    Search the document corpus using vector similarity.

    Returns the most relevant chunks together with
    their source document and similarity score.
    """

    query_embedding = embed_text(query)

    # Convert Python list -> PostgreSQL vector literal
    vector = "[" + ",".join(map(str, query_embedding)) + "]"

    try:
        conn = get_connection()
    except psycopg.Error as exc:
        raise DocumentSearchConnectionError(
            "Could not connect to the document-search database."
        ) from exc

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    c.content,
                    d.source,
                    e.embedding <=> %s::vector AS score
                FROM embeddings e
                JOIN chunks c
                    ON e.chunk_id = c.id
                JOIN documents d
                    ON c.document_id = d.id
                ORDER BY score ASC
                LIMIT %s;
                """,
                (
                    vector,
                    top_k,
                ),
            )

            rows = cur.fetchall()

            return [
                {
                    "content": content,
                    "source": source,
                    "score": float(score),
                }
                for content, source, score in rows
            ]

    except psycopg.Error as exc:
        raise DocumentSearchQueryError(
            "Document search query failed."
        ) from exc

    finally:
        conn.close()