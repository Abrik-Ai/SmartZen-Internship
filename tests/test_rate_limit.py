import pytest
from fastapi import HTTPException

from app.rate_limit import RateLimiter


def test_allows_up_to_the_limit() -> None:
    limiter = RateLimiter(max_requests=20, window_seconds=60, clock=lambda: 0.0)
    for _ in range(20):
        limiter.check("user-a")  # should not raise


def test_request_over_the_limit_raises_429_with_retry_after() -> None:
    limiter = RateLimiter(max_requests=20, window_seconds=60, clock=lambda: 0.0)
    for _ in range(20):
        limiter.check("user-a")

    with pytest.raises(HTTPException) as exc_info:
        limiter.check("user-a")

    assert exc_info.value.status_code == 429
    assert "Retry-After" in exc_info.value.headers
    assert int(exc_info.value.headers["Retry-After"]) > 0


def test_limit_is_tracked_per_key() -> None:
    limiter = RateLimiter(max_requests=1, window_seconds=60, clock=lambda: 0.0)
    limiter.check("user-a")
    limiter.check("user-b")  # different user, independent budget - should not raise

    with pytest.raises(HTTPException):
        limiter.check("user-a")


def test_old_requests_age_out_of_the_window() -> None:
    now = [0.0]
    limiter = RateLimiter(max_requests=1, window_seconds=60, clock=lambda: now[0])

    limiter.check("user-a")
    with pytest.raises(HTTPException):
        limiter.check("user-a")

    now[0] = 60.1  # window has fully passed
    limiter.check("user-a")  # should not raise


def test_retry_after_shrinks_as_the_window_ages() -> None:
    now = [0.0]
    limiter = RateLimiter(max_requests=1, window_seconds=60, clock=lambda: now[0])

    limiter.check("user-a")
    now[0] = 40.0
    with pytest.raises(HTTPException) as exc_info:
        limiter.check("user-a")

    # 60s window, 40s already elapsed -> ~20s left before the oldest hit ages out
    assert int(exc_info.value.headers["Retry-After"]) <= 20
