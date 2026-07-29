from datetime import UTC, datetime, timedelta

from pydantic import BaseModel

from app.backend_client import BackendClient
from app.models.generated import RoomRef


def date_time(range_value: str) -> tuple[datetime, datetime | None]:
    now = datetime.now(UTC)
    midnight_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    one_day = timedelta(days=1)
    seven_days = timedelta(days=7)
    midnight_tomorrow = midnight_today + one_day
    midnight_week = midnight_today + seven_days
    

    if range_value == "today":
        from_time = midnight_today
        to_time = midnight_tomorrow
        return from_time, to_time
    elif range_value == "week":
        from_time = midnight_today
        to_time = midnight_week
        return from_time, to_time
    elif range_value == "upcoming":
        from_time = now
        to_time = None
        return from_time, to_time
    else:
        raise ValueError(f"Invalid range: {range_value!r}")

class ScheduleResponse(BaseModel):
    id: str
    course_label: str
    start_time: str
    end_time: str 
    room: RoomRef

async def get_my_schedule(
        range_value: str, token: str, client: BackendClient
        ) -> list[ScheduleResponse]:
    from_time, to_time = date_time(range_value)
    from_time_str = from_time.isoformat()
    if to_time is not None:
        to_time_str = to_time.isoformat()
    else:
        to_time_str = None
    schedules = await client.get_schedules(token, from_time=from_time_str, to_time=to_time_str)
    schedules_endpoint = [
    ScheduleResponse(
        id=schedule.id,
        course_label=schedule.course_label,
        start_time=schedule.start_time.isoformat(),
        end_time=schedule.end_time.isoformat(),
        room=schedule.room,
    )
    for schedule in schedules
    ]
    schedules_endpoint.sort(key=lambda s: s.start_time)
    schedules_endpoint = schedules_endpoint[:20]
    return schedules_endpoint
