import os
import time
import uuid
from unittest.mock import AsyncMock, patch

import jwt
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _token(sub: str | None = None) -> str:
    payload = {
        "sub": sub or f"user-{uuid.uuid4()}",
        "role": "INSTRUCTOR",
        "exp": int(time.time()) + 100,
    }
    return jwt.encode(payload, os.environ["JWT_ACCESS_SECRET"], algorithm="HS256")


def test_requires_auth() -> None:
    response = client.get("/assistant/status")
    assert response.status_code == 401


def test_returns_enabled_true() -> None:
    with patch("app.main.is_assistant_enabled", new=AsyncMock(return_value=True)):
        response = client.get(
            "/assistant/status", headers={"Authorization": f"Bearer {_token()}"}
        )
    assert response.status_code == 200
    assert response.json() == {"enabled": True}


def test_returns_enabled_false() -> None:
    with patch("app.main.is_assistant_enabled", new=AsyncMock(return_value=False)):
        response = client.get(
            "/assistant/status", headers={"Authorization": f"Bearer {_token()}"}
        )
    assert response.status_code == 200
    assert response.json() == {"enabled": False}


def test_any_role_is_accepted() -> None:
    for role in ["INSTRUCTOR", "STUDENT", "SUPER_ADMIN", "FACULTY_COORDINATOR"]:
        payload = {"sub": f"user-{uuid.uuid4()}", "role": role, "exp": int(time.time()) + 100}
        token = jwt.encode(payload, os.environ["JWT_ACCESS_SECRET"], algorithm="HS256")
        with patch("app.main.is_assistant_enabled", new=AsyncMock(return_value=True)):
            response = client.get("/assistant/status", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200, role


def test_21st_request_in_a_minute_gets_429_with_retry_after() -> None:
    token = _token(sub=f"rate-limit-test-{uuid.uuid4()}")
    headers = {"Authorization": f"Bearer {token}"}

    with patch("app.main.is_assistant_enabled", new=AsyncMock(return_value=True)):
        for _ in range(20):
            response = client.get("/assistant/status", headers=headers)
            assert response.status_code == 200

        response = client.get("/assistant/status", headers=headers)

    assert response.status_code == 429
    assert "Retry-After" in response.headers
    assert int(response.headers["Retry-After"]) > 0


def test_rate_limit_is_per_user_token() -> None:
    token_a = _token(sub=f"rate-limit-a-{uuid.uuid4()}")
    token_b = _token(sub=f"rate-limit-b-{uuid.uuid4()}")

    with patch("app.main.is_assistant_enabled", new=AsyncMock(return_value=True)):
        for _ in range(20):
            response = client.get(
                "/assistant/status", headers={"Authorization": f"Bearer {token_a}"}
            )
            assert response.status_code == 200

        # user A is now at budget, user B should be unaffected
        response = client.get("/assistant/status", headers={"Authorization": f"Bearer {token_b}"})
        assert response.status_code == 200
