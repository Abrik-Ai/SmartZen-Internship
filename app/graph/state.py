from typing import Any, TypedDict


class GraphState(TypedDict):
    message: str
    history: list[dict[str, str]]
    caller: str
    token: str 
    reply: str
    toolCall: dict[str, Any] | None
    tool_result: Any | None
    tool_calls: int
    loop_count: int 