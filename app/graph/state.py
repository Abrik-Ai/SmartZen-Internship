from typing import Any, TypedDict

from app.tools.room_context import RoomContext


class GraphState(TypedDict):
    message: str
    history: list[dict[str, str]]
    caller: str
    token: str 
    reply: str
    toolCall: dict[str, Any] | None
    tool_result: Any | None
    tool_name: str | None
    tool_calls: int 
    loop_count: int
    room_context: RoomContext | None