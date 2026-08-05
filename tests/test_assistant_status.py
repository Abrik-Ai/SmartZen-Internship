from dataclasses import dataclass, field
from unittest.mock import AsyncMock, patch

import httpx
import ollama
import pytest

from app.assistant_status import AssistantStatusCache, probe_ollama


@dataclass
class FakeModel:
    model: str


@dataclass
class FakeListResponse:
    models: list[FakeModel] = field(default_factory=list)


# ---- probe_ollama -----------------------------------------------------


@pytest.mark.asyncio
async def test_probe_false_when_base_url_not_set() -> None:
    assert await probe_ollama(None, "qwen2.5:3b") is False
    assert await probe_ollama("", "qwen2.5:3b") is False


@pytest.mark.asyncio
async def test_probe_true_when_model_present() -> None:
    fake_response = FakeListResponse(
        models=[FakeModel(model="qwen2.5:3b"), FakeModel(model="llama3")]
    )
    with patch(
        "app.assistant_status.ollama.AsyncClient.list",
        new=AsyncMock(return_value=fake_response),
    ):
        assert await probe_ollama("http://localhost:11434", "qwen2.5:3b") is True


@pytest.mark.asyncio
async def test_probe_false_when_model_missing() -> None:
    fake_response = FakeListResponse(models=[FakeModel(model="llama3")])
    with patch(
        "app.assistant_status.ollama.AsyncClient.list",
        new=AsyncMock(return_value=fake_response),
    ):
        assert await probe_ollama("http://localhost:11434", "qwen2.5:3b") is False


@pytest.mark.asyncio
async def test_probe_false_when_server_unreachable() -> None:
    with patch(
        "app.assistant_status.ollama.AsyncClient.list",
        new=AsyncMock(side_effect=ConnectionError("Ollama refused the connection")),
    ):
        assert await probe_ollama("http://localhost:11434", "qwen2.5:3b") is False


@pytest.mark.asyncio
async def test_probe_false_when_server_times_out() -> None:
    with patch(
        "app.assistant_status.ollama.AsyncClient.list",
        new=AsyncMock(side_effect=httpx.TimeoutException("too slow")),
    ):
        assert await probe_ollama("http://localhost:11434", "qwen2.5:3b") is False


@pytest.mark.asyncio
async def test_probe_false_on_response_error() -> None:
    with patch(
        "app.assistant_status.ollama.AsyncClient.list",
        new=AsyncMock(side_effect=ollama.ResponseError("boom", 500)),
    ):
        assert await probe_ollama("http://localhost:11434", "qwen2.5:3b") is False


# ---- AssistantStatusCache ----------------------------------------------


@pytest.mark.asyncio
async def test_cache_calls_probe_on_first_use() -> None:
    probe = AsyncMock(return_value=True)
    cache = AssistantStatusCache(probe=probe, ttl_seconds=30, clock=lambda: 0.0)

    assert await cache.is_enabled() is True
    assert probe.call_count == 1


@pytest.mark.asyncio
async def test_cache_does_not_reping_within_ttl() -> None:
    probe = AsyncMock(return_value=True)
    now = [0.0]
    cache = AssistantStatusCache(probe=probe, ttl_seconds=30, clock=lambda: now[0])

    await cache.is_enabled()
    now[0] = 10.0  # still inside the 30s window
    await cache.is_enabled()
    now[0] = 29.9
    await cache.is_enabled()

    assert probe.call_count == 1  # never re-pinged


@pytest.mark.asyncio
async def test_cache_repings_after_ttl_expires() -> None:
    probe = AsyncMock(return_value=True)
    now = [0.0]
    cache = AssistantStatusCache(probe=probe, ttl_seconds=30, clock=lambda: now[0])

    await cache.is_enabled()
    now[0] = 30.1  # past the 30s window
    await cache.is_enabled()

    assert probe.call_count == 2


@pytest.mark.asyncio
async def test_cache_reflects_updated_probe_result_after_expiry() -> None:
    probe = AsyncMock(side_effect=[True, False])
    now = [0.0]
    cache = AssistantStatusCache(probe=probe, ttl_seconds=30, clock=lambda: now[0])

    assert await cache.is_enabled() is True
    now[0] = 31.0
    assert await cache.is_enabled() is False
