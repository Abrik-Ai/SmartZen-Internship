from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest

from app.backend_client import BackendClient
from app.models.proposals import EndSessionProposal, ExtendProposal, RoomChangeProposal
from app.tools.proposals import (
    NoActiveSessionResult,
    RoomNotFoundResult,
    propose_end_session,
    propose_extend,
    propose_room_change,
)


class MockResponse:
    def __init__(self, data: dict) -> None:
        self.data = data

    def json(self) -> dict:
        return self.data

    def raise_for_status(self) -> None:
        pass


def make_client() -> BackendClient:
    return BackendClient(base_url="http://testserver")


# ---------------------------------------------------------------------------
# propose_extend
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_propose_extend_uses_scheduled_end_when_later_than_now() -> None:
    """New end time = scheduled end (still in the future) + requested minutes."""
    scheduled_end = datetime.now(UTC) + timedelta(minutes=15)
    mock_sessions = {
        "sessions": [
            {
                "id": "sess-1",
                "room_id": "r1",
                "start_time": "2026-07-29T10:00:00Z",
                "end_time": scheduled_end.isoformat(),
                "status": "active",
            }
        ]
    }

    with patch(
        "app.backend_client.httpx.AsyncClient.get",
        new_callable=AsyncMock,
        return_value=MockResponse(mock_sessions),
    ):
        result = await propose_extend(20, "test_token", make_client())

    assert isinstance(result, ExtendProposal)
    assert result.session_id == "sess-1"
    # Base was the scheduled end (later than "now"), plus 20 minutes.
    assert result.until == scheduled_end + timedelta(minutes=20)


@pytest.mark.asyncio
async def test_propose_extend_uses_now_when_session_is_overdue() -> None:
    """If the scheduled end has already passed, base off now instead."""
    scheduled_end = datetime.now(UTC) - timedelta(minutes=30)
    mock_sessions = {
        "sessions": [
            {
                "id": "sess-1",
                "room_id": "r1",
                "start_time": "2026-07-29T10:00:00Z",
                "end_time": scheduled_end.isoformat(),
                "status": "active",
            }
        ]
    }

    before = datetime.now(UTC)
    with patch(
        "app.backend_client.httpx.AsyncClient.get",
        new_callable=AsyncMock,
        return_value=MockResponse(mock_sessions),
    ):
        result = await propose_extend(10, "test_token", make_client())
    after = datetime.now(UTC)

    assert isinstance(result, ExtendProposal)
    # `until` should be ~10 minutes from "now" (between before/after), not
    # 10 minutes from the stale scheduled_end.
    assert before + timedelta(minutes=10) <= result.until <= after + timedelta(minutes=10)


@pytest.mark.asyncio
async def test_propose_extend_no_active_session() -> None:
    mock_sessions: dict = {"sessions": []}

    with patch(
        "app.backend_client.httpx.AsyncClient.get",
        new_callable=AsyncMock,
        return_value=MockResponse(mock_sessions),
    ):
        result = await propose_extend(15, "test_token", make_client())

    assert isinstance(result, NoActiveSessionResult)
    assert "extend" in result.message.lower()


# ---------------------------------------------------------------------------
# propose_end_session
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_propose_end_session_with_active_session() -> None:
    mock_sessions = {
        "sessions": [
            {
                "id": "sess-1",
                "room_id": "r1",
                "start_time": "2026-07-29T10:00:00Z",
                "status": "active",
            }
        ]
    }

    with patch(
        "app.backend_client.httpx.AsyncClient.get",
        new_callable=AsyncMock,
        return_value=MockResponse(mock_sessions),
    ):
        result = await propose_end_session("test_token", make_client())

    assert isinstance(result, EndSessionProposal)
    assert result.session_id == "sess-1"


@pytest.mark.asyncio
async def test_propose_end_session_no_active_session_does_not_error() -> None:
    """With no active session, this should explain that rather than raise
    or propose ending a session that doesn't exist."""
    mock_sessions: dict = {"sessions": []}

    with patch(
        "app.backend_client.httpx.AsyncClient.get",
        new_callable=AsyncMock,
        return_value=MockResponse(mock_sessions),
    ):
        result = await propose_end_session("test_token", make_client())

    assert isinstance(result, NoActiveSessionResult)
    assert "end" in result.message.lower()


# ---------------------------------------------------------------------------
# propose_room_change
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_propose_room_change_resolves_name_case_insensitively() -> None:
    mock_rooms = {
        "rooms": [
            {
                "id": "r2",
                "name": "Room 202",
                "building": "B",
                "type": "lecture",
                "next_class": {
                    "start_time": "2026-07-29T11:00:00Z",
                    "course_label": "Math 101",
                },
            }
        ]
    }

    with patch(
        "app.backend_client.httpx.AsyncClient.get",
        new_callable=AsyncMock,
        return_value=MockResponse(mock_rooms),
    ):
        result = await propose_room_change("  room 202  ", "test_token", make_client())

    assert isinstance(result, RoomChangeProposal)
    assert result.to_room_id == "r2"
    assert result.to_room_name == "Room 202"


@pytest.mark.asyncio
async def test_propose_room_change_unknown_room_offers_search_instead_of_erroring() -> None:
    mock_rooms: dict = {"rooms": []}

    with patch(
        "app.backend_client.httpx.AsyncClient.get",
        new_callable=AsyncMock,
        return_value=MockResponse(mock_rooms),
    ):
        result = await propose_room_change("Nonexistent Hall", "test_token", make_client())

    assert isinstance(result, RoomNotFoundResult)
    assert result.requested_name == "Nonexistent Hall"
    assert result.suggestion == "search_free_rooms"


# ---------------------------------------------------------------------------
# Proof that these tools only ever propose - they never mutate state.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_proposal_tools_never_call_a_mutating_http_method() -> None:
    """
    Every write-shaped HTTP verb is patched to blow up if called. If any
    proposal tool ever tried to actually perform the extend/end/room-change
    instead of just proposing it, this test would fail loudly.
    """
    mock_sessions = {
        "sessions": [
            {
                "id": "sess-1",
                "room_id": "r1",
                "start_time": "2026-07-29T10:00:00Z",
                "end_time": (datetime.now(UTC) + timedelta(minutes=10)).isoformat(),
                "status": "active",
            }
        ]
    }
    mock_rooms = {
        "rooms": [
            {
                "id": "r2",
                "name": "Room 202",
                "building": "B",
                "type": "lecture",
                "next_class": {
                    "start_time": "2026-07-29T11:00:00Z",
                    "course_label": "Math 101",
                },
            }
        ]
    }

    def refuse(*args: object, **kwargs: object) -> None:
        raise AssertionError("proposal tools must never call a mutating HTTP method")

    with (
        patch("app.backend_client.httpx.AsyncClient.post", side_effect=refuse),
        patch("app.backend_client.httpx.AsyncClient.put", side_effect=refuse),
        patch("app.backend_client.httpx.AsyncClient.patch", side_effect=refuse),
        patch("app.backend_client.httpx.AsyncClient.delete", side_effect=refuse),
        patch(
            "app.backend_client.httpx.AsyncClient.get",
            new_callable=AsyncMock,
            side_effect=[
                MockResponse(mock_sessions),
                MockResponse(mock_sessions),
                MockResponse(mock_rooms),
            ],
        ),
    ):
        client = make_client()
        extend_result = await propose_extend(20, "test_token", client)
        end_result = await propose_end_session("test_token", client)
        room_result = await propose_room_change("Room 202", "test_token", client)

    # And, just as importantly: every write path returns a proposal object,
    # never a "done"/"success" style result.
    assert isinstance(extend_result, ExtendProposal)
    assert isinstance(end_result, EndSessionProposal)
    assert isinstance(room_result, RoomChangeProposal)


def test_backend_client_has_no_mutating_session_or_room_methods() -> None:
    """
    Structural guarantee: BackendClient doesn't even expose a method that
    could extend a session, end a session, or change a room. The proposal
    tools are built only on top of the read-only `get_active_sessions` and
    `get_empty_rooms` methods.
    """
    forbidden_method_names = {
        "extend_session",
        "end_session",
        "change_room",
        "update_session",
        "checkin",
    }
    client_methods = {name for name in dir(BackendClient) if not name.startswith("_")}

    assert forbidden_method_names.isdisjoint(client_methods)
