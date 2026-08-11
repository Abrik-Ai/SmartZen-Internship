from typing import NoReturn
from unittest.mock import AsyncMock, patch

import pytest

from app.ollama_warmup import keep_alive_loop, pull_model_if_missing, start_warmup


@pytest.mark.asyncio
async def test_pull_model_if_missing() -> None:
    """Test that missing model triggers a pull."""
    mock_client = AsyncMock()
    mock_client.list.return_value = type("FakeResponse", (), {"models": []})()

    with patch("app.ollama_warmup.ollama.AsyncClient", return_value=mock_client):
        await pull_model_if_missing()

    mock_client.pull.assert_called_once_with(model="qwen2.5:3b")


@pytest.mark.asyncio
async def test_pull_model_if_already_exists() -> None:
    """Test that existing model doesn't trigger a pull."""
    mock_client = AsyncMock()
    mock_model = type("FakeModel", (), {"model": "qwen2.5:3b"})
    mock_client.list.return_value = type("FakeResponse", (), {"models": [mock_model]})()

    with patch("app.ollama_warmup.ollama.AsyncClient", return_value=mock_client):
        await pull_model_if_missing()

    mock_client.pull.assert_not_called()


@pytest.mark.asyncio
async def test_pull_model_handles_exception_gracefully() -> None:
    """Test that pull_model_if_missing doesn't crash on errors."""
    mock_client = AsyncMock()
    mock_client.list.side_effect = Exception("Ollama not running")

    with patch("app.ollama_warmup.ollama.AsyncClient", return_value=mock_client):
        # Should not raise an exception
        await pull_model_if_missing()


@pytest.mark.asyncio
async def test_start_warmup_calls_pull_and_creates_task() -> None:
    """Test that start_warmup triggers the pull and keep-alive."""
    with patch("app.ollama_warmup.pull_model_if_missing", new=AsyncMock()) as mock_pull, \
         patch("app.ollama_warmup.asyncio.create_task") as mock_create_task:

        await start_warmup()

        mock_pull.assert_awaited_once()
        mock_create_task.assert_called_once()


@pytest.mark.asyncio
async def test_keep_alive_loop_pings_and_continues() -> None:
    """Test that keep_alive_loop sends pings and continues running."""
    mock_chat = AsyncMock(return_value=None)

    with patch("app.ollama_warmup.ollama.AsyncClient") as mock_client:
        mock_client.return_value.chat = mock_chat

        async def break_after_loop(*args: object, **kwargs: object) -> NoReturn:
            raise StopAsyncIteration

        with patch("app.ollama_warmup.asyncio.sleep", side_effect=break_after_loop):
            try:
                await keep_alive_loop()
            except StopAsyncIteration:
                pass

        mock_chat.assert_called_with(
            model="qwen2.5:3b",
            messages=[{"role": "user", "content": "ping"}],
            stream=False
        )


@pytest.mark.asyncio
async def test_keep_alive_loop_handles_exceptions() -> None:
    """Test that keep_alive_loop continues even if ping fails."""
    mock_chat = AsyncMock(side_effect=Exception("Ollama down"))

    with patch("app.ollama_warmup.ollama.AsyncClient") as mock_client:
        mock_client.return_value.chat = mock_chat

        async def break_after_loop(*args: object, **kwargs: object) -> NoReturn:
            raise StopAsyncIteration

        with patch("app.ollama_warmup.asyncio.sleep", side_effect=break_after_loop):
            try:
                await keep_alive_loop()
            except StopAsyncIteration:
                pass

        mock_chat.assert_called_with(
            model="qwen2.5:3b",
            messages=[{"role": "user", "content": "ping"}],
            stream=False
        )