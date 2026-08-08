"""
Tools module for interacting with the backend API.
"""

from app.tools.proposals import (
    NoActiveSessionResult,
    RoomNotFoundResult,
    propose_end_session,
    propose_extend,
    propose_room_change,
)
from app.tools.rooms import RoomStatusResponse, find_free_rooms, get_room_status
from app.tools.schedule import ScheduleResponse, get_my_schedule

from .search_docs import documentation_search as documentation_search

__all__ = [
    "find_free_rooms",
    "get_my_schedule",
    "get_room_status",
    "NoActiveSessionResult",
    "RoomNotFoundResult",
    "RoomStatusResponse",
    "ScheduleResponse",
    "propose_end_session",
    "propose_extend",
    "propose_room_change",
]
