from unittest.mock import AsyncMock, patch

import pytest
from hypothesis import given
from hypothesis import strategies as st

from app.backend_client import BackendClient
from app.tools.proposals import RoomChangeProposal, RoomNotFoundResult, propose_room_change

FREE_ROOM = {
    "rooms": [
        {
            "id": "r1",
            "name": "Room 101",
            "building": "B",
            "type": "lecture",
            "next_class": {
                "start_time": "2026-07-29T11:00:00Z",
                "course_label": "Math 101",
            },
        }
    ]
}


class MockResponse:
    def __init__(self, data: dict) -> None:
        self.data = data

    def json(self) -> dict:
        return self.data

    def raise_for_status(self) -> None:
        pass


@given(
        room_name=st.one_of(
            st.text(),
            st.sampled_from(["Room 101", "room 101", "  ROOM 101  "]),
        )
    )
@pytest.mark.asyncio
async def test_proposal_never_names_a_room(room_name: str,) -> None:
    """Scope is inherited from the token: a proposal may only ever name a room
    returned by the caller's own authenticated free-room read, never a string
    the caller supplied."""
    with patch(
        "app.backend_client.httpx.AsyncClient.get",
        new_callable=AsyncMock,
        return_value=MockResponse(FREE_ROOM),
    ):
        result = await propose_room_change(
            room_name, "test_token", BackendClient(base_url="http://testserver")
        )

    if isinstance(result, RoomChangeProposal):
        assert result.to_room_id == "r1"
        assert result.to_room_name == "Room 101"
    else:
        assert isinstance(result, RoomNotFoundResult)