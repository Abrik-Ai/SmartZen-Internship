from datetime import datetime

from pydantic import BaseModel


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

