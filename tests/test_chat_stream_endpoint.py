import os
import time
import uuid
from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import AsyncMock, patch

import jwt
from fastapi.testclient import TestClient

from app.chat_stream import ChatStreamError
from app.main import app

client = TestClient(app)


def _token() -> str:
    payload = {
        "sub": f"user-{uuid.uuid4()}",
        "role": "INSTRUCTOR",
        "exp": int(time.time()) + 100,
    }
    return jwt.encode(
        payload,
        os.environ["JWT_ACCESS_SECRET"],
        algorithm="HS256",
    )


def _auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {_token()}"}


async def _fake_stream(*args: Any, **kwargs: Any) -> AsyncIterator[str]:
    for token in ["Hel", "lo", " world"]:
        yield token


def test_returns_disabled_json_body_when_assistant_is_disabled() -> None:
    with patch(
        "app.main.is_assistant_enabled",
        new=AsyncMock(return_value=False),
    ):
        response = client.post(
            "/assistant/chat/stream",
            json={"messages": [{"role": "user", "content": "hi"}]},
            headers=_auth_headers(),
        )

    assert response.status_code == 200
    assert response.json() == {"enabled": False}
    assert response.headers["content-type"].startswith("application/json")


def test_streams_tokens_when_enabled() -> None:
    with (
        patch(
            "app.main.is_assistant_enabled",
            new=AsyncMock(return_value=True),
        ),
        patch(
            "app.main.stream_chat_tokens",
            new=_fake_stream,
        ),
    ):
        response = client.post(
            "/assistant/chat/stream",
            json={"messages": [{"role": "user", "content": "hi"}]},
            headers=_auth_headers(),
        )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith(
        "text/event-stream"
    )
    body = response.text
    assert "event: token" in body
    assert '"token": "Hel"' in body
    assert "event: done" in body


def test_mid_stream_failure_ends_with_disabled_frame_not_a_500() -> None:
    async def _failing_stream(
        *args: Any,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        yield "partial"
        raise ChatStreamError("Ollama died mid-generation")

    with (
        patch(
            "app.main.is_assistant_enabled",
            new=AsyncMock(return_value=True),
        ),
        patch(
            "app.main.stream_chat_tokens",
            new=_failing_stream,
        ),
    ):
        response = client.post(
            "/assistant/chat/stream",
            json={"messages": [{"role": "user", "content": "hi"}]},
            headers=_auth_headers(),
        )

    assert response.status_code == 200
    body = response.text
    assert "event: token" in body
    assert "event: disabled" in body
    assert '"enabled": false' in body


def test_queue_full_returns_disabled_json_without_opening_a_stream() -> None:
    from app import main as main_module

    with (
        patch(
            "app.main.is_assistant_enabled",
            new=AsyncMock(return_value=True),
        ),
        patch.object(
            main_module,
            "MAX_CONCURRENT_STREAMS",
            0,
        ),
    ):
        response = client.post(
            "/assistant/chat/stream",
            json={"messages": [{"role": "user", "content": "hi"}]},
            headers=_auth_headers(),
        )

    assert response.status_code == 200
    assert response.json() == {"enabled": False}
    assert response.headers["content-type"].startswith("application/json")


def test_requires_auth() -> None:
    response = client.post(
        "/assistant/chat/stream",
        json={"messages": [{"role": "user", "content": "hi"}]},
    )
    assert response.status_code == 401


def test_metrics_requires_auth() -> None:
    response = client.get("/assistant/metrics")
    assert response.status_code == 401


def test_metrics_returns_expected_shape() -> None:
    response = client.get(
        "/assistant/metrics",
        headers=_auth_headers(),
    )

    assert response.status_code == 200

    body = response.json()

    assert "latency" in body
    assert "queue_depth" in body
    assert "gpu" in body
    assert isinstance(body["queue_depth"], int)


def test_metrics_reflects_recorded_request_latency() -> None:
    client.get("/health")

    response = client.get(
        "/assistant/metrics",
        headers=_auth_headers(),
    )

    body = response.json()

    assert "/health" in body["latency"]
    assert body["latency"]["/health"]["count"] >= 1
    assert "p50_ms" in body["latency"]["/health"]