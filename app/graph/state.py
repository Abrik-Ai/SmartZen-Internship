from typing import Any, TypedDict


class GraphState(TypedDict):
    message: str
    history: list[dict[str, str]]
    caller: str

    reply: str
    scheduleLookup: dict[str, str] | None

    tool_result: list[dict[str, Any]] | None
    tool_calls: int

    loop_count: int