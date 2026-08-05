from unittest.mock import AsyncMock, patch

import pytest

from app.backend_client import BackendClient
from app.tools.rooms import find_free_rooms, get_room_status


class MockResponse:
    def __init__(self, data: dict) -> None:
        self.data = data
    
    def json(self) -> dict:
        return self.data
    
    def raise_for_status(self) -> None:
        pass


@pytest.mark.asyncio
async def test_find_free_rooms() -> None:
    """Test that find_free_rooms returns room data."""
    mock_data: dict = {
        "rooms": [
            {
                "id": "r1",
                "name": "Room 101",
                "building": "A",
                "type": "lecture",
                "next_class": {
                    "start_time": "2026-07-29T11:00:00Z",
                    "course_label": "Math 101"
                }
            }
        ]
    }
    
    with patch(
        "app.backend_client.httpx.AsyncClient.get",
        new_callable=AsyncMock,
        return_value=MockResponse(mock_data)
    ):
        client = BackendClient(base_url="http://testserver")
        result = await find_free_rooms(30, "test_token", client)
    
    assert len(result) == 1
    assert result[0].id == "r1"
    assert result[0].name == "Room 101"


@pytest.mark.asyncio
async def test_get_room_status_no_active_session() -> None:
    """Test that get_room_status returns empty when no session."""
    mock_sessions: dict = {"sessions": []}
    
    with patch(
        "app.backend_client.httpx.AsyncClient.get",
        new_callable=AsyncMock,
        return_value=MockResponse(mock_sessions)
    ):
        client = BackendClient(base_url="http://testserver")
        result = await get_room_status("test_token", client)
    
    assert result.session is None
    assert result.telemetry is None


@pytest.mark.asyncio
async def test_get_room_status_with_active_session() -> None:
    """Test that get_room_status returns session and telemetry."""
    mock_sessions: dict = {
        "sessions": [
            {"room_id": "r1", "start_time": "2026-07-29T10:00:00Z", "status": "active"}
        ]
    }
    mock_telemetry: dict = {
        "temperature": 22.5,
        "humidity": 45.0,
        "co2": 420
    }
    
    with patch(
        "app.backend_client.httpx.AsyncClient.get",
        new_callable=AsyncMock
    ) as mock_get:
        mock_get.side_effect = [
            MockResponse(mock_sessions),
            MockResponse(mock_telemetry)
        ]
        
        client = BackendClient(base_url="http://testserver")
        result = await get_room_status("test_token", client)
    
    assert result.session is not None
    assert result.session["room_id"] == "r1"
    assert result.telemetry is not None
    assert result.telemetry["temperature"] == 22.5