from app.rag.chunking import chunk_text


def test_chunk_text_splits_text_into_overlapping_chunks() -> None:
    text = "one two three four five six seven eight"

    result = chunk_text(text, chunk_size=3, overlap=1)

    assert result == [
        "one two three",
        "three four five",
        "five six seven",
        "seven eight",
    ]


def test_chunk_text_merges_a_short_tail_chunk_when_it_is_tiny() -> None:
    text = " ".join(f"word{i}" for i in range(1, 12))

    result = chunk_text(text, chunk_size=10, overlap=0)

    assert result == [" ".join(f"word{i}" for i in range(1, 12))]


def test_chunk_text_keeps_a_tail_chunk_when_it_is_big_enough() -> None:
    text = " ".join(f"word{i}" for i in range(1, 15))

    result = chunk_text(text, chunk_size=10, overlap=0)

    assert result == [
        "word1 word2 word3 word4 word5 word6 word7 word8 word9 word10",
        "word11 word12 word13 word14",
    ]


def test_chunk_text_respects_the_requested_overlap() -> None:
    text = "one two three four five six seven eight"

    result = chunk_text(text, chunk_size=4, overlap=1)

    assert result == [
        "one two three four",
        "four five six seven",
        "seven eight",
    ]