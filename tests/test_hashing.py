from hashlib import sha256

from app.rag.hashing import hash_text


def test_hash_text_matches_reference_sha256() -> None:
    """hash_text should just be sha256 hex-digest of the UTF-8 bytes."""
    text = "SmartZen manages classrooms, labs, and their smart devices."
    expected = sha256(text.encode("utf-8")).hexdigest()

    assert hash_text(text) == expected


def test_hash_text_is_deterministic() -> None:
    """Hashing the same text twice must give the same hash."""
    text = "Sessions end automatically at the scheduled end time."

    assert hash_text(text) == hash_text(text)


def test_hash_text_differs_for_different_text() -> None:
    """Different content should (almost certainly) hash differently."""
    assert hash_text("Room 101 is free.") != hash_text("Room 102 is free.")


def test_hash_text_is_sensitive_to_whitespace_and_case() -> None:
    """A hash is over exact bytes - trivial formatting differences must
    change it, since it's used to detect "has this document changed"."""
    base = "Instructors check into a room by scanning a QR code."

    assert hash_text(base) != hash_text(base.upper())
    assert hash_text(base) != hash_text(base + " ")
    assert hash_text(base) != hash_text(base + "\n")


def test_hash_text_empty_string() -> None:
    """Empty input is valid and matches the known sha256 of b''."""
    assert hash_text("") == sha256(b"").hexdigest()


def test_hash_text_handles_unicode() -> None:
    """Non-ASCII text should hash consistently via UTF-8 encoding."""
    text = "Кипр — это остров. 北塞浦路斯"
    expected = sha256(text.encode("utf-8")).hexdigest()

    assert hash_text(text) == expected


def test_hash_text_returns_64_char_hex_digest() -> None:
    """sha256 hex digests are always 64 lowercase hex characters."""
    digest = hash_text("any content at all")

    assert len(digest) == 64
    assert all(c in "0123456789abcdef" for c in digest)
