from app.rag.evaluate import EvalSummary, QuestionScore, score_question, summarize_scores
from app.rag.search import SearchResult


def make_result(source: str, content: str, score: float = 0.1) -> SearchResult:
    return SearchResult(source=source, content=content, score=score)


# ---------------------------------------------------------------------------
# score_question
# ---------------------------------------------------------------------------


def test_score_question_hit_at_rank_1() -> None:
    """The correct chunk is the very first result -> hit at every cutoff."""
    results = [
        make_result("backend_DOCS.md", "Instructors check in using a QR code."),
        make_result("frontend_DOCS.md", "Something unrelated."),
    ]

    score = score_question(results, expected_source="backend_DOCS.md", expected_contains="QR")

    assert score == QuestionScore(hit1=True, hit3=True, hit5=True)


def test_score_question_hit_only_at_rank_3() -> None:
    """Correct chunk shows up third -> miss at 1, hit at 3 and 5."""
    results = [
        make_result("frontend_DOCS.md", "Not it."),
        make_result("frontend_DOCS.md", "Also not it."),
        make_result("backend_DOCS.md", "Notifications are pushed over WebSocket."),
    ]

    score = score_question(
        results, expected_source="backend_DOCS.md", expected_contains="WebSocket"
    )

    assert score == QuestionScore(hit1=False, hit3=True, hit5=True)


def test_score_question_hit_only_at_rank_5() -> None:
    """Correct chunk shows up fifth -> miss at 1 and 3, hit at 5."""
    results = [
        make_result("frontend_DOCS.md", "Not it."),
        make_result("frontend_DOCS.md", "Not it."),
        make_result("frontend_DOCS.md", "Not it."),
        make_result("frontend_DOCS.md", "Not it."),
        make_result("backend_DOCS.md", "Alarm rules can be set per room."),
    ]

    score = score_question(results, expected_source="backend_DOCS.md", expected_contains="alarm")

    assert score == QuestionScore(hit1=False, hit3=False, hit5=True)


def test_score_question_no_match_anywhere() -> None:
    """None of the results match -> miss at every cutoff."""
    results = [
        make_result("frontend_DOCS.md", "Not it."),
        make_result("frontend_DOCS.md", "Still not it."),
    ]

    score = score_question(results, expected_source="backend_DOCS.md", expected_contains="MQTT")

    assert score == QuestionScore(hit1=False, hit3=False, hit5=False)


def test_score_question_empty_results() -> None:
    """No results returned at all -> miss at every cutoff, no crash."""
    score = score_question([], expected_source="backend_DOCS.md", expected_contains="QR")

    assert score == QuestionScore(hit1=False, hit3=False, hit5=False)


def test_score_question_matching_content_wrong_source_does_not_count() -> None:
    """Content matches the expected substring but comes from the wrong
    source document - that should NOT count as a match."""
    results = [
        make_result("frontend_DOCS.md", "Instructors check in using a QR code."),
    ]

    score = score_question(results, expected_source="backend_DOCS.md", expected_contains="QR")

    assert score == QuestionScore(hit1=False, hit3=False, hit5=False)


def test_score_question_right_source_wrong_content_does_not_count() -> None:
    """Right source document, but the expected substring isn't present -
    that should NOT count as a match either."""
    results = [
        make_result("backend_DOCS.md", "This chunk talks about something else entirely."),
    ]

    score = score_question(results, expected_source="backend_DOCS.md", expected_contains="QR")

    assert score == QuestionScore(hit1=False, hit3=False, hit5=False)


def test_score_question_is_case_insensitive() -> None:
    """expect_contains matching should ignore case, same as the original
    inline logic did (`expected_contains.lower() in r["content"].lower()`)."""
    results = [make_result("backend_DOCS.md", "DEVICE STATE IS SYNCED OVER MQTT.")]

    score = score_question(results, expected_source="backend_DOCS.md", expected_contains="mqtt")

    assert score["hit1"] is True


def test_score_question_only_considers_first_five_for_hit5() -> None:
    """A match at rank 6+ should NOT count toward hit3 or hit5 - only the
    first five results are considered (mirrors search_docs(top_k=5))."""
    results = [make_result("frontend_DOCS.md", "irrelevant")] * 5 + [
        make_result("backend_DOCS.md", "Alarm rules can be set per room.")
    ]

    score = score_question(results, expected_source="backend_DOCS.md", expected_contains="alarm")

    assert score == QuestionScore(hit1=False, hit3=False, hit5=False)


# ---------------------------------------------------------------------------
# summarize_scores
# ---------------------------------------------------------------------------


def test_summarize_scores_counts_hits_per_cutoff() -> None:
    scores = [
        QuestionScore(hit1=True, hit3=True, hit5=True),
        QuestionScore(hit1=False, hit3=True, hit5=True),
        QuestionScore(hit1=False, hit3=False, hit5=True),
        QuestionScore(hit1=False, hit3=False, hit5=False),
    ]

    summary = summarize_scores(scores)

    assert summary == EvalSummary(total=4, hit1=1, hit3=2, hit5=3)


def test_summarize_scores_empty_list() -> None:
    """No questions evaluated -> all-zero summary, no division or crash."""
    summary = summarize_scores([])

    assert summary == EvalSummary(total=0, hit1=0, hit3=0, hit5=0)


def test_summarize_scores_all_hits() -> None:
    scores = [QuestionScore(hit1=True, hit3=True, hit5=True) for _ in range(3)]

    summary = summarize_scores(scores)

    assert summary == EvalSummary(total=3, hit1=3, hit3=3, hit5=3)


def test_summarize_scores_all_misses() -> None:
    scores = [QuestionScore(hit1=False, hit3=False, hit5=False) for _ in range(3)]

    summary = summarize_scores(scores)

    assert summary == EvalSummary(total=3, hit1=0, hit3=0, hit5=0)


# ---------------------------------------------------------------------------
# End-to-end (pure) - score_question feeding into summarize_scores, still
# with no database or model involved.
# ---------------------------------------------------------------------------


def test_score_then_summarize_matches_manual_expectation() -> None:
    dataset: list[tuple[list[SearchResult], str, str]] = [
        (
            [make_result("backend_DOCS.md", "Uses QR codes to check in.")],
            "backend_DOCS.md",
            "QR",
        ),
        (
            [make_result("frontend_DOCS.md", "No QR mention here.")],
            "backend_DOCS.md",
            "QR",
        ),
    ]

    scores = [
        score_question(results, expected_source, expected_contains)
        for results, expected_source, expected_contains in dataset
    ]
    summary = summarize_scores(scores)

    assert summary == EvalSummary(total=2, hit1=1, hit3=1, hit5=1)
