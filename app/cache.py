"""Generic async TTL-cached boolean check.

Not specific to Ollama or the assistant status — any async probe that
returns a bool can be wrapped here. `probe` and `clock` are injectable so
callers can test without real waiting or a real network call.
"""
from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable


class AssistantStatusCache:
    """Caches the result of `probe()` for `ttl_seconds`."""

    def __init__(
        self,
        probe: Callable[[], Awaitable[bool]],
        ttl_seconds: float,
        clock: Callable[[], float],
    ) -> None:
        self._probe = probe
        self._ttl_seconds = ttl_seconds
        self._clock = clock
        self._lock = asyncio.Lock()
        self._enabled = False
        self._checked_at: float | None = None

    async def is_enabled(self) -> bool:
        async with self._lock:
            now = self._clock()
            if self._checked_at is not None and now - self._checked_at < self._ttl_seconds:
                return self._enabled
            self._enabled = await self._probe()
            self._checked_at = now
            return self._enabled