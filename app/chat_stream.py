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

from app.tracing import RunTrace


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
    trace: RunTrace | None = None,
) -> AsyncIterator[str]:
    """Yields response tokens one at a time.

    Checks `is_disconnected()` between tokens; the moment it's true, this
    breaks out and closes the upstream Ollama stream rather than draining it.

    If `trace` is provided, it will be updated with the results:
    - tokens: number of tokens streamed
    - reply: the complete reply
    - is_valid_json: whether the reply is valid JSON
    - tool_chosen: if a tool was used (placeholder for future use)
    - latency: automatically calculated when trace.finish() is called
    """
    client = ollama.AsyncClient(host=base_url, timeout=timeout_seconds)
    collected_tokens: list[str] = []
    tool_chosen: str | None = None

    try:
        stream = await client.chat(model=model, messages=messages, stream=True)
    except (ConnectionError, ollama.ResponseError, httpx.TimeoutException, httpx.HTTPError) as e:
        # Update trace with error if provided
        if trace:
            trace.finish(
                reply="",
                tokens=0,
                tool=None,
                is_valid_json=False,
                error=str(e)
            )
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
                collected_tokens.append(token)
                yield token
    except (ConnectionError, ollama.ResponseError, httpx.TimeoutException, httpx.HTTPError) as e:
        # Update trace with error if provided
        if trace:
            trace.finish(
                reply="".join(collected_tokens),
                tokens=len(collected_tokens),
                tool=tool_chosen,
                is_valid_json=False,
                error=str(e)
            )
        raise ChatStreamError(str(e)) from e
    finally:
        # Always close the upstream stream on our way out — success,
        # disconnect, or error — so Ollama's own generation actually stops
        # rather than continuing to run with nobody reading it.
        aclose = getattr(stream, "aclose", None)
        if aclose is not None:
            with contextlib.suppress(Exception):
                await aclose()

        # Complete the trace with results (on success)
        if trace:
            full_reply = "".join(collected_tokens)
            # Check if the reply is valid JSON
            import json
            is_valid = False
            try:
                json.loads(full_reply)
                is_valid = True
            except (json.JSONDecodeError, ValueError):
                pass
            
            trace.finish(
                reply=full_reply,
                tokens=len(collected_tokens),
                tool=tool_chosen,
                is_valid_json=is_valid,
                error=None
            )