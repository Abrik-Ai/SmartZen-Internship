from pathlib import Path

from app.rag.chunking import chunk_text
from app.rag.database import (
    document_exists,
    get_connection,
    insert_chunk,
    insert_document,
    insert_embedding,
)
from app.rag.embeddings import embed_text
from app.rag.hashing import hash_text

DOCS_DIR = Path("docs")


def ingest_documents() -> None:

    conn = get_connection()

    if not DOCS_DIR.exists():
        print(f"Directory '{DOCS_DIR}' does not exist.")
        return

    markdown_files = sorted(DOCS_DIR.glob("*.md"))

    if not markdown_files:
        print("No markdown documents found.")
        return

    for file_path in markdown_files:

        print("=" * 60)
        print(f"Reading: {file_path.name}")

        text = file_path.read_text(encoding="utf-8")
        file_hash = hash_text(text)

        if document_exists(conn, file_hash):
            print("Already ingested. Skipping.")
            continue

        document_id = insert_document(
            conn,
            source=file_path.name,
            title=file_path.stem,
            content_hash=file_hash,
        )

        chunks = chunk_text(text)

        print(f"SHA256 : {file_hash}")
        print(f"Chunks : {len(chunks)}")

        for index, chunk in enumerate(chunks):

            chunk_id = insert_chunk(
                conn,
                document_id=document_id,
                chunk_index=index,
                content=chunk,
                token_count=len(chunk.split()),
            )

            embedding = embed_text(chunk)

            insert_embedding(
                conn,
                chunk_id=chunk_id,
                embedding=embedding,
            )

            preview = chunk[:80].replace("\n", " ")

            if len(chunk) > 80:
                preview += "..."

            print(f"  Chunk {index + 1}: {preview}")

    conn.close()

    print("=" * 60)
    print("Ingestion complete.")


if __name__ == "__main__":
    ingest_documents()