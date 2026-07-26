from unittest.mock import patch

from app.backend_client import BackendClient
from app.models.generated import Schedule


class MockResponse:
    def __init__(self, data: list[dict]):
        self._data = data

    def json(self) -> list[dict]:
        return self._data

def test_get_schedules() -> None:
        mock_data = [ 
            {
                "id": "1",
                "course_label": "Math 101",
                "start_time": "2026-07-27T10:00:00Z",
                "end_time": "2026-07-27T11:00:00Z",
                "room": {"id": "r1", "name": "101", "building": "A"},
                "instructor": {"id": "t1", "name": "Ms. Lee"},
            }
        ]

        with patch("app.backend_client.httpx.get", return_value=MockResponse(mock_data)):
            client = BackendClient(base_url="http://testserver")
            result = client.get_schedules(token="test_token")

        assert result == [Schedule.model_validate(mock_data[0])]