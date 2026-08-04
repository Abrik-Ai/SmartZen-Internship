"""20 requests/minute per user token. Over the limit -> 429 with Retry-After.

Sliding-window log, in-memory, keyed by the caller's user_id (from the
verified JWT — never anything client-supplied). This is process-local: fine
for a single uvicorn worker, but if smartzen-ai ever runs multiple workers
or replicas, this needs to move to something shared (e.g. Redis) or each
process will get its own 20/min budget.

No lock is needed around RateLimiter.check(): it's synchronous, contains no
`await`, so under asyncio's single-threaded event loop nothing else can run
between reading and updating `_hits` — it can't be interleaved.
"""

from __future__ import annotations

import math
import time
from collections import defaultdict

from fastapi import Depends, HTTPException, Request, status

from app.auth import verify_jwt

RATE_LIMIT_MAX_REQUESTS = 20
RATE_LIMIT_WINDOW_SECONDS = 60.0


class RateLimiter:
    def __init__(
        self,
        max_requests: int = RATE_LIMIT_MAX_REQUESTS,
        window_seconds: float = RATE_LIMIT_WINDOW_SECONDS,
        clock: object = time.monotonic,
    ) -> None:
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._clock = clock
        self._hits: dict[str, list[float]] = defaultdict(list)

    def check(self, key: str) -> None:
        """Raises HTTPException(429, headers={"Retry-After": ...}) if `key` is over budget."""
        now = self._clock()  # type: ignore[operator]
        timestamps = self._hits[key]

        cutoff = now - self._window_seconds
        while timestamps and timestamps[0] <= cutoff:
            timestamps.pop(0)

        if len(timestamps) >= self._max_requests:
            retry_after = max(1, math.ceil(timestamps[0] + self._window_seconds - now))
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=(
                    f"Rate limit exceeded: {self._max_requests} requests "
                    f"per {int(self._window_seconds)}s per user"
                ),
                headers={"Retry-After": str(retry_after)},
            )

        timestamps.append(now)


_limiter = RateLimiter()


async def rate_limit(request: Request, _auth: None = Depends(verify_jwt)) -> None:
    """FastAPI dependency. Depends on verify_jwt itself so request.state.auth
    is always populated before we read it — order isn't left to chance."""
    _limiter.check(request.state.auth.user_id)
