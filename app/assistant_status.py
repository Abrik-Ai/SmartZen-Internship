"""Backs GET /assistant/status.

`enabled` is only true when all three hold:
  1. OLLAMA_BASE_URL is set in config
  2. the Ollama server answers
  3. OLLAMA_MODEL is present in Ollama's model list

We ask Ollama for its model list (GET /api/tags under the hood) rather than
pinging some separate health route: if that call succeeds we already know
the server answered, and we get the model list in the same round trip. That
covers checks 2 and 3 with a single request instead of two.

Because that's a real network call, the result is cached for ~30s
(AssistantStatusCache) so normal traffic to /assistant/status doesn't hit
Ollama on every request.
"""

from __future__ import annotations

import time

import httpx
import ollama

from app.cache import AssistantStatusCache
from app.config import OLLAMA_BASE_URL
from app.runtime_config import get_pinned_model

CACHE_TTL_SECONDS = 30.0
OLLAMA_PING_TIMEOUT_SECONDS = 5.0


async def probe_ollama(base_url: str | None, model: str) -> bool:
    """Hits Ollama for real. Only called on a cache miss — see AssistantStatusCache."""
    if not base_url:
        return False  # condition 1: OLLAMA_BASE_URL not set

    client = ollama.AsyncClient(host=base_url, timeout=OLLAMA_PING_TIMEOUT_SECONDS)
    try:
        response = await client.list()
    except (ConnectionError, ollama.ResponseError, httpx.TimeoutException, httpx.HTTPError):
        return False  # condition 2: server didn't answer

    return any(m.model == model for m in response.models)  # condition 3

async def _default_probe() -> bool:
    return await probe_ollama(OLLAMA_BASE_URL, get_pinned_model())


_status_cache = AssistantStatusCache(
    probe=_default_probe, 
    ttl_seconds=CACHE_TTL_SECONDS, 
    clock=time.perf_counter
    )


async def is_assistant_enabled() -> bool:
    return await _status_cache.is_enabled()
