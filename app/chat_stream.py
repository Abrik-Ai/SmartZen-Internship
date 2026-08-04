"""Token-by-token chat streaming with real mid-generation cancellation.

Cancelling here means more than "the client stopped rendering": when the
caller disconnects, we stop reading from Ollama and call `.aclose()` on its
streaming generator. That's what actually closes the HTTP connection to
Ollama — and Ollama treats an aborted connection as "stop generating", so
cancellation stops compute, not just what shows up on screen.

Any failure — connect error, model missing (404), timeout, or anything else
Ollama-side — raises ChatStreamError. Callers turn that into the standard
"disabled" response instead of a 500; see app/main.py's chat_stream route.
"""

from __future__ import annotations

import contextlib
from collections.abc import AsyncIterator, Awaitable, Callable

import httpx
import ollama


class ChatStreamError(Exception):
    """Any failure while trying to stream a chat reply — connect error,
    model missing, timeout, or an unexpected Ollama-side error."""


async def stream_chat_tokens(
    messages: list[dict[str, str]],
    *,
    base_url: str,
    model: str,
    is_disconnected: Callable[[], Awaitable[bool]],
    timeout_seconds: float = 60.0,
) -> AsyncIterator[str]:
    """Yields response tokens one at a time.

    Checks `is_disconnected()` between tokens; the moment it's true, this
    breaks out and closes the upstream Ollama stream rather than draining it.
    """
    client = ollama.AsyncClient(host=base_url, timeout=timeout_seconds)

    try:
        stream = await client.chat(model=model, messages=messages, stream=True)
    except (ConnectionError, ollama.ResponseError, httpx.TimeoutException, httpx.HTTPError) as e:
        raise ChatStreamError(str(e)) from e

    try:
        while True:
            if await is_disconnected():
                break
            try:
                chunk = await stream.__anext__()
            except StopAsyncIteration:
                break
            token = chunk.message.content or ""
            if token:
                yield token
    except (ConnectionError, ollama.ResponseError, httpx.TimeoutException, httpx.HTTPError) as e:
        raise ChatStreamError(str(e)) from e
    finally:
        # Always close the upstream stream on our way out — success,
        # disconnect, or error — so Ollama's own generation actually stops
        # rather than continuing to run with nobody reading it.
        aclose = getattr(stream, "aclose", None)
        if aclose is not None:
            with contextlib.suppress(Exception):
                await aclose()
