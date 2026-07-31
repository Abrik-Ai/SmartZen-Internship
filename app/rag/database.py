import os
import uuid

import psycopg
from dotenv import load_dotenv

load_dotenv()

DB_NAME = os.getenv("DB_NAME", "smartzen")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")


def get_connection() -> psycopg.Connection:
    """
    Create and return a PostgreSQL connection.
    """
    return psycopg.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
    )


def document_exists(conn: psycopg.Connection, content_hash: str) -> bool:
    """
    Check whether a document with the given hash already exists.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT 1
            FROM documents
            WHERE content_hash = %s
            """,
            (content_hash,),
        )
        return cur.fetchone() is not None


def insert_document(
    conn: psycopg.Connection,
    source: str,
    title: str,
    content_hash: str,
) -> uuid.UUID:
    """
    Insert a document and return its UUID.
    """
    document_id = uuid.uuid4()

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO documents
            (id, source, title, content_hash)
            VALUES (%s, %s, %s, %s)
            """,
            (
                document_id,
                source,
                title,
                content_hash,
            ),
        )

    conn.commit()
    return document_id


def insert_chunk(
    conn: psycopg.Connection,
    document_id: uuid.UUID,
    chunk_index: int,
    content: str,
    token_count: int,
) -> uuid.UUID:
    """
    Insert one chunk and return its UUID.
    """
    chunk_id = uuid.uuid4()

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO chunks
            (id, document_id, chunk_index, content, token_count)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                chunk_id,
                document_id,
                chunk_index,
                content,
                token_count,
            ),
        )

    conn.commit()
    return chunk_id


def insert_embedding(
    conn: psycopg.Connection,
    chunk_id: uuid.UUID,
    embedding: list[float],
) -> None:
    """
    Insert an embedding for a chunk.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO embeddings
            (chunk_id, embedding)
            VALUES (%s, %s)
            """,
            (
                chunk_id,
                embedding,
            ),
        )

    conn.commit()