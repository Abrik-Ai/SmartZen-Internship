import pytest

from app.graph.graph import build_graph


def make_state(message: str) -> dict:
    return {
        "message": message,
        "history": [],
        "caller": "INSTRUCTOR",
        "reply": "",
        "scheduleLookup": None,
        "tool_result": None,
        "tool_calls": 0,
        "loop_count": 0,
    }


@pytest.mark.asyncio
async def test_schedule_today_uses_schedule_tool():
    graph = build_graph()

    state = make_state("What's my schedule today?")

    result = await graph.ainvoke(state)

    assert result["scheduleLookup"] == {"range": "today"}
    assert result["tool_result"] is not None
    assert result["tool_calls"] == 1


@pytest.mark.asyncio
async def test_normal_message_does_not_use_schedule_tool():
    graph = build_graph()

    state = make_state("Hello")

    result = await graph.ainvoke(state)

    assert result["scheduleLookup"] is None
    assert result["tool_result"] is None
    assert result["tool_calls"] == 0