from datetime import UTC, datetime

from pydantic import BaseModel

from app.backend_client import BackendClient
from app.tools.rooms import get_room_status


class SensorReadings(BaseModel):
    """Model representing sensor readings in a room."""
    temperature: float | None = None
    humidity: float | None = None
    co2: float | None = None
    lux: float | None = None
    presence: bool | None = None
    window_open: bool | None = None
    timestamp: datetime

class RoomContext(BaseModel):
    """Model representing the context of a room."""
    room_name: str
    current_class: str 
    start_time: datetime
    end_time: datetime 
    minutes_left: int
    readings: SensorReadings

async def get_room_context(token: str, client: BackendClient) -> RoomContext | None:
    """Fetch the context of a room from the backend."""
    status = await get_room_status(token, client)
    if status.session is None:
        return None
    
    schedule = status.session.get("schedule")
    if schedule is None:
        return None

    room_name = status.session["room"]["name"]
    current_class = schedule["course_label"]
    start_time=datetime.fromisoformat(status.session["started_at"].replace("Z", "+00:00"))
    end_time = datetime.fromisoformat(schedule["end_time"].replace("Z", "+00:00"))
    minutes_left = int((end_time - datetime.now(UTC)).total_seconds() / 60)
    telemetry = status.telemetry or {}
    readings = SensorReadings(
        temperature=telemetry.get("temperature"),
        humidity=telemetry.get("humidity"),
        co2=telemetry.get("co2"),
        lux=telemetry.get("lux"),
        presence=telemetry.get("presence"),
        window_open=telemetry.get("window_open"),
        timestamp=telemetry.get("timestamp") or datetime.now(UTC)
    )

    return RoomContext(
        room_name=room_name,
        current_class=current_class,
        start_time=start_time,
        end_time=end_time,
        minutes_left=minutes_left,
        readings=readings,
    )
