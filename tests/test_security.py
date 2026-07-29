from unittest.mock import AsyncMock, patch

import pytest

from app.backend_client import BackendClient
from app.tools.schedule import get_my_schedule


class MockResponse:
    def __init__(self, data: list[dict]):
        self.data = data

    def json(self) -> list[dict]:
        return self.data

    def raise_for_status(self) -> None:
        pass
@pytest.mark.asyncio
async def test_token_forward_a() -> None:
    with patch(
        "app.backend_client.httpx.AsyncClient.get",
          new_callable=AsyncMock, 
          return_value=MockResponse([])) as mock_get:
        client = BackendClient(base_url="http://testserver")
        await get_my_schedule("week", "token-for-instructor-a", client)

        sent_headers = mock_get.call_args.kwargs["headers"]
        assert sent_headers["Authorization"] == "Bearer token-for-instructor-a"

@pytest.mark.asyncio
async def test_token_forward_b() -> None:
    with patch(
        "app.backend_client.httpx.AsyncClient.get", 
         new_callable=AsyncMock, 
         return_value=MockResponse([])) as mock_get:
        client = BackendClient(base_url="http://testserver")
        await get_my_schedule("week", "token-for-instructor-b", client)

        sent_headers = mock_get.call_args.kwargs["headers"]
        assert sent_headers["Authorization"] == "Bearer token-for-instructor-b"


# This suite was manually verified to catch a real regression: a caller's
# token was temporarily hardcoded in get_schedules(), both tests failed with
# a clear diagnostic, then the hack was reverted       