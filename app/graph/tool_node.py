from typing import Any

from app.graph.state import GraphState
from app.tools.schedule_stub import schedule_lookup_stub


async def run_schedule_tool(state: GraphState) -> dict[str, Any]:
    """Run at most one schedule lookup for this turn."""

    lookup = state.get("scheduleLookup")

    if lookup is None:
        return {
            "tool_result": None,
            "tool_calls": state.get("tool_calls", 0),
        }

    # The graph has exactly one tool field, so this is the single
    # allowed tool call for the current turn.
    result = await schedule_lookup_stub(lookup["range"])

    return {
        "tool_result": result,
        "tool_calls": state.get("tool_calls", 0) + 1,
    }