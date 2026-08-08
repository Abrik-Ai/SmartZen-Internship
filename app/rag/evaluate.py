from pathlib import Path
from typing import TypedDict

import yaml

from app.rag.search import SearchResult, search_docs

TEST_FILE = Path("app/rag/test_questions.yaml")


class QuestionScore(TypedDict):
    """Whether a single question was a hit at each cutoff."""

    hit1: bool
    hit3: bool
    hit5: bool


class EvalSummary(TypedDict):
    """Aggregated hit counts across every question in the eval set."""

    total: int
    hit1: int
    hit3: int
    hit5: int


def score_question(
    results: list[SearchResult],
    expected_source: str,
    expected_contains: str,
) -> QuestionScore:
    """
    Score a single question's retrieval results against the expected
    source document and expected substring.

    A result "matches" when it comes from `expected_source` AND its
    content contains `expected_contains` (case-insensitively). This is
    a pure function - it doesn't call search_docs or touch the database,
    it only scores whatever results it's given.

    Args:
        results: Ranked retrieval results, best match first.
        expected_source: The source document the correct chunk should
            come from.
        expected_contains: A substring the correct chunk's content
            should contain (case-insensitive).

    Returns:
        A QuestionScore with hit1/hit3/hit5 booleans, where hitN is
        True if any of the top-N results matched.
    """
    expected_contains_lower = expected_contains.lower()

    matches = [
        r["source"] == expected_source and expected_contains_lower in r["content"].lower()
        for r in results
    ]

    return QuestionScore(
        hit1=bool(matches) and matches[0],
        hit3=any(matches[:3]),
        hit5=any(matches[:5]),
    )


def summarize_scores(scores: list[QuestionScore]) -> EvalSummary:
    """
    Aggregate per-question scores into totals across the whole eval set.

    Pure function - just sums booleans, no I/O.

    Args:
        scores: One QuestionScore per evaluated question.

    Returns:
        An EvalSummary with the total question count and hit counts at
        each cutoff.
    """
    return EvalSummary(
        total=len(scores),
        hit1=sum(1 for s in scores if s["hit1"]),
        hit3=sum(1 for s in scores if s["hit3"]),
        hit5=sum(1 for s in scores if s["hit5"]),
    )


def evaluate() -> None:

    tests = yaml.safe_load(TEST_FILE.read_text())

    scores = [
        score_question(
            search_docs(test["question"], top_k=5),
            expected_source=test["expect_source"],
            expected_contains=test["expect_contains"],
        )
        for test in tests
    ]

    summary = summarize_scores(scores)

    print(f"Total Questions : {summary['total']}")
    print(f"Hit@1 : {summary['hit1']}/{summary['total']}")
    print(f"Hit@3 : {summary['hit3']}/{summary['total']}")
    print(f"Hit@5 : {summary['hit5']}/{summary['total']}")


if __name__ == "__main__":
    evaluate()