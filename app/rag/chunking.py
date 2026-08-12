

def chunk_text(
    text: str,
    chunk_size: int = 500,
    overlap: int = 50,
) -> list[str]:

    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")

    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    words = text.split()

    if not words:
        return []

    chunks = []
    stride = chunk_size - overlap

    for start in range(0, len(words), stride):
        chunk_words = words[start:start + chunk_size]

        if not chunk_words:
            break

        chunks.append(" ".join(chunk_words))

    if len(chunks) > 1:
        last_chunk_words = chunks[-1].split()
        smallest_chunk_to_keep = max(1, chunk_size // 5)

        if len(last_chunk_words) < smallest_chunk_to_keep:
            chunks[-2] += " " + chunks[-1]
            chunks.pop()

    return chunks