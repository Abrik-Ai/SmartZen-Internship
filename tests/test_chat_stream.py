from collections.abc import AsyncIterable
from dataclasses import dataclass
from typing import Any
from unittest.mock import AsyncMock, patch

import httpx
import ollama
import pytest

from app.chat_stream import ChatStreamError, stream_chat_tokens


@dataclass
class FakeMessage:
    content: str | None


@dataclass
class FakeChunk:
    message: FakeMessage


class FakeStream:
    """Stands in for what `await ollama.AsyncClient().chat(stream=True)` returns:
    an async generator of chunks, with a real `.aclose()`."""

    def __init__(
        self,
        tokens: list[str | None],
        fail_after: int | None = None,
        fail_with: Exception | None = None,
    ) -> None:
        self._chunks = [FakeChunk(FakeMessage(t)) for t in tokens]
        self._index = 0
        self._fail_after = fail_after
        self._fail_with = fail_with
        self.pulled = 0
        self.closed = False

    def __aiter__(self) -> "FakeStream":
        return self

    async def __anext__(self) -> FakeChunk:
        if self._fail_after is not None and self._index == self._fail_after:
            if self._fail_with is not None:
                raise self._fail_with
            raise StopAsyncIteration

        if self._index >= len(self._chunks):
            raise StopAsyncIteration

        chunk = self._chunks[self._index]
        self._index += 1
        self.pulled += 1
        return chunk

    async def aclose(self) -> None:
        self.closed = True


def _never_disconnected() -> AsyncMock:
    return AsyncMock(return_value=False)


async def _collect(gen: AsyncIterable[Any]) -> list[Any]:
    return [item async for item in gen]


@pytest.mark.asyncio
async def test_yields_tokens_in_order_and_closes_upstream_on_success() -> None:
    stream = FakeStream(["Hel", "lo", " world"])

    with patch(
        "app.chat_stream.ollama.AsyncClient.chat",
        new=AsyncMock(return_value=stream),
    ):
        tokens = await _collect(
            stream_chat_tokens(
                [{"role": "user", "content": "hi"}],
                base_url="http://localhost:11434",
                model="qwen2.5:3b",
                is_disconnected=_never_disconnected(),
            )
        )

    assert tokens == ["Hel", "lo", " world"]
    assert stream.closed is True


@pytest.mark.asyncio
async def test_skips_empty_content_chunks() -> None:
    stream = FakeStream(["Hi", None, "", " there"])

    with patch(
        "app.chat_stream.ollama.AsyncClient.chat",
        new=AsyncMock(return_value=stream),
    ):
        tokens = await _collect(
            stream_chat_tokens(
                [{"role": "user", "content": "hi"}],
                base_url="http://localhost:11434",
                model="qwen2.5:3b",
                is_disconnected=_never_disconnected(),
            )
        )

    assert tokens == ["Hi", " there"]


@pytest.mark.asyncio
async def test_disconnect_stops_pulling_more_tokens_and_closes_upstream() -> None:
    """Proof of real cancellation: once disconnected, we never pull the
    remaining tokens out of the upstream stream at all."""
    stream = FakeStream(["a", "b", "c", "d", "e"])
    disconnected_after_two = AsyncMock(side_effect=[False, False, True])

    with patch(
        "app.chat_stream.ollama.AsyncClient.chat",
        new=AsyncMock(return_value=stream),
    ):
        tokens = await _collect(
            stream_chat_tokens(
                [{"role": "user", "content": "hi"}],
                base_url="http://localhost:11434",
                model="qwen2.5:3b",
                is_disconnected=disconnected_after_two,
            )
        )

    assert tokens == ["a", "b"]
    assert stream.pulled == 2
    assert stream.closed is True


@pytest.mark.asyncio
async def test_connect_failure_raises_chat_stream_error() -> None:
    with patch(
        "app.chat_stream.ollama.AsyncClient.chat",
        new=AsyncMock(side_effect=ConnectionError("refused")),
    ):
        with pytest.raises(ChatStreamError):
            await _collect(
                stream_chat_tokens(
                    [{"role": "user", "content": "hi"}],
                    base_url="http://localhost:11434",
                    model="qwen2.5:3b",
                    is_disconnected=_never_disconnected(),
                )
            )


@pytest.mark.asyncio
async def test_model_not_found_raises_chat_stream_error() -> None:
    with patch(
        "app.chat_stream.ollama.AsyncClient.chat",
        new=AsyncMock(
            side_effect=ollama.ResponseError("model not found", 404)
        ),
    ):
        with pytest.raises(ChatStreamError):
            await _collect(
                stream_chat_tokens(
                    [{"role": "user", "content": "hi"}],
                    base_url="http://localhost:11434",
                    model="does-not-exist",
                    is_disconnected=_never_disconnected(),
                )
            )


@pytest.mark.asyncio
async def test_mid_stream_timeout_raises_and_still_closes_upstream() -> None:
    stream = FakeStream(
        ["partial"],
        fail_after=1,
        fail_with=httpx.TimeoutException("slow"),
    )

    with patch(
        "app.chat_stream.ollama.AsyncClient.chat",
        new=AsyncMock(return_value=stream),
    ):
        gen = stream_chat_tokens(
            [{"role": "user", "content": "hi"}],
            base_url="http://localhost:11434",
            model="qwen2.5:3b",
            is_disconnected=_never_disconnected(),
        )

        tokens = []

        with pytest.raises(ChatStreamError):
            async for token in gen:
                tokens.append(token)

    assert tokens == ["partial"]
    assert stream.closed is True

@pytest.mark.asyncio
async def test_trace_is_updated_on_success() -> None:
    """Test that trace is updated with results on successful stream."""
    from app.tracing import create_trace

    stream = FakeStream(["Hello", " world"])
    trace = create_trace("Say hi", "qwen2.5:3b")

    with patch(
        "app.chat_stream.ollama.AsyncClient.chat",
        new=AsyncMock(return_value=stream),
    ):
        tokens = await _collect(
            stream_chat_tokens(
                [{"role": "user", "content": "hi"}],
                base_url="http://localhost:11434",
                model="qwen2.5:3b",
                is_disconnected=_never_disconnected(),
                trace=trace,
            )
        )

    assert trace.reply == "Hello world"
    assert trace.tokens == len(tokens)
    assert trace.end_time is not None
    assert trace.error is None


@pytest.mark.asyncio
async def test_trace_is_updated_on_connect_error() -> None:
    """Test that trace is updated with error when connection fails."""
    from app.tracing import create_trace

    trace = create_trace("Say hi", "qwen2.5:3b")

    with patch(
        "app.chat_stream.ollama.AsyncClient.chat",
        new=AsyncMock(side_effect=ConnectionError("refused")),
    ):
        with pytest.raises(ChatStreamError):
            await _collect(
                stream_chat_tokens(
                    [{"role": "user", "content": "hi"}],
                    base_url="http://localhost:11434",
                    model="qwen2.5:3b",
                    is_disconnected=_never_disconnected(),
                    trace=trace,
                )
            )

    assert trace.reply == ""
    assert trace.tokens == 0
    assert trace.error is not None
    assert "refused" in trace.error


@pytest.mark.asyncio
async def test_trace_checks_json_validity() -> None:
    """Test that trace correctly identifies valid JSON."""
    from app.tracing import create_trace

    stream = FakeStream(['{"answer": "hello"}'])
    trace = create_trace("Say hi", "qwen2.5:3b")

    with patch(
        "app.chat_stream.ollama.AsyncClient.chat",
        new=AsyncMock(return_value=stream),
    ):
        await _collect(
            stream_chat_tokens(
                [{"role": "user", "content": "hi"}],
                base_url="http://localhost:11434",
                model="qwen2.5:3b",
                is_disconnected=_never_disconnected(),
                trace=trace,
            )
        )

    assert trace.is_valid_json is True


@pytest.mark.asyncio
async def test_trace_checks_invalid_json() -> None:
    """Test that trace correctly identifies invalid JSON."""
    from app.tracing import create_trace

    stream = FakeStream(["This is not JSON"])
    trace = create_trace("Say hi", "qwen2.5:3b")

    with patch(
        "app.chat_stream.ollama.AsyncClient.chat",
        new=AsyncMock(return_value=stream),
    ):
        await _collect(
            stream_chat_tokens(
                [{"role": "user", "content": "hi"}],
                base_url="http://localhost:11434",
                model="qwen2.5:3b",
                is_disconnected=_never_disconnected(),
                trace=trace,
            )
        )

    assert trace.is_valid_json is False