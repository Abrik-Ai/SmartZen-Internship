
from pydantic import BaseModel

from app.backend_client import BackendClient
from app.models.generated import EmptyRoom


class RoomStatusResponse(BaseModel):
    """Response model for room status."""
    session: dict | None = None
    telemetry: dict | None = None


async def find_free_rooms(
    minutes_needed: int,
    token: str,
    client: BackendClient,
    start_time: str | None = None
) -> list[EmptyRoom]:
    """
    Find free rooms for a given time window.
    
    Args:
        minutes_needed: How many minutes the room is needed for
        token: User authentication token
        client: Backend client instance
        start_time: Optional start time (ISO format)
    
    Returns:
        List of EmptyRoom objects
    """
    rooms = await client.get_empty_rooms(
        token=token,
        minutes=minutes_needed,
        start=start_time
    )
    return rooms


async def get_room_status(
    token: str,
    client: BackendClient
) -> RoomStatusResponse:
    """
    Get the user's active session and room status.
    
    Args:
        token: User authentication token
        client: Backend client instance
    
    Returns:
        RoomStatusResponse with session and telemetry data
    """
    sessions = await client.get_active_sessions(token)

    if not sessions or not sessions.get("sessions"):
        return RoomStatusResponse(session=None, telemetry=None)

    active_session = sessions["sessions"][0]
    room_id = active_session.get("room_id")

    if not room_id:
        return RoomStatusResponse(session=active_session, telemetry=None)

    telemetry = await client.get_latest_telemetry(token, room_id)

    return RoomStatusResponse(
        session=active_session,
        telemetry=telemetry
    )