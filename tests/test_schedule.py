from datetime import UTC, datetime, timedelta
from unittest.mock import patch, AsyncMock

import pytest

from app.backend_client import BackendClient
from app.tools.schedule import date_time, get_my_schedule


def test_date_time_today() -> None:
    from_time, to_time = date_time("today")
    if to_time is None:
            raise AssertionError("to_time should not be None for 'week' range")
    else:
        gap =  to_time - from_time 
    assert gap == timedelta(days=1)
    assert from_time.hour == 0 and from_time.minute == 0 and from_time.second == 0

def test_date_time_week() -> None:
    from_time, to_time = date_time("week")
    if to_time is None:
        raise AssertionError("to_time should not be None for 'week' range")
    else:
        gap = to_time - from_time 
    assert gap == timedelta(days=7)
    assert from_time.hour == 0 and from_time.minute == 0 and from_time.second == 0

def test_date_time_upcoming() -> None:
    from_time, to_time = date_time("upcoming")
    now_check = datetime.now(UTC)
    assert now_check - from_time < timedelta(seconds=2)
    assert to_time is None

def test_date_time_invalid() -> None:
    with pytest.raises(ValueError):
        date_time("invalid_range")


class MockResponse:
    def __init__(self, data: list[dict]):
        self.data = data

    def json(self) -> list[dict]:
        return self.data

    def raise_for_status(self) -> None:
        pass  # Simulate a successful response (status code 200)

@pytest.mark.asyncio
async def test_get_my_schedule() -> None:
    mock_data = []
    for i in range(25):
       mock_data.append({
        "id": str(i),
        "course_label": f"Course {i}",
        "start_time": (datetime.now(UTC) + timedelta(days=i)).isoformat(),
        "end_time": (datetime.now(UTC) + timedelta(days=i, hours=1)).isoformat(),
        "room": {"id": f"r{i}", "name": f"Room {i}", "building": f"Building {i}"},
        "instructor": {"id": f"t{i}", "name": f"Instructor {i}"},
    })
    mock_data.reverse() #to assert that actually same 20 items captured

    with patch("app.backend_client.httpx.AsyncClient.get", new_callable=AsyncMock, return_value=MockResponse(mock_data)):
        client = BackendClient(base_url="http://testserver")
        result = await get_my_schedule("week", "test_token", client)
        
    assert len(result) == 20

    for i in range(len(result) - 1):
        assert result[i].start_time <= result[i + 1].start_time