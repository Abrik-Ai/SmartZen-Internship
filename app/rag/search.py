from typing import TypedDict

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

    conn = get_connection()

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

    finally:
        conn.close()