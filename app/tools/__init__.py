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
from app.tools.room_context import RoomContext, get_room_context
from app.tools.rooms import RoomStatusResponse, find_free_rooms, get_room_status
from app.tools.schedule import ScheduleResponse, get_my_schedule
from app.tools.search_docs import documentation_search

__all__ = [
    "documentation_search",
    "find_free_rooms",
    "get_my_schedule",
    "get_room_status",
    "NoActiveSessionResult",
    "RoomNotFoundResult",
    "RoomStatusResponse",
    "ScheduleResponse",
    "get_room_context",
    "RoomContext",
    "propose_end_session",
    "propose_extend",
    "propose_room_change",
]
