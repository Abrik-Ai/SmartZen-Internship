import json
from dataclasses import dataclass
from unittest.mock import patch

import pytest

from app.graph.graph import build_graph


@dataclass
class MockResponse:
    content: str


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
async def test_schedule_today_uses_schedule_tool() -> None:
    graph = build_graph()
    state = make_state("What's my schedule today?")

    mock_content = json.dumps(
        {
            "reply": "I'll check your schedule for today.",
            "scheduleLookup": {"range": "today"},
        }
    )

    with patch(
        "app.graph.nodes.ChatOllama.invoke",
        return_value=MockResponse(content=mock_content),
    ):
        result = await graph.ainvoke(state)

    assert result["scheduleLookup"] == {"range": "today"}
    assert result["tool_result"] is not None
    assert result["tool_calls"] == 1


@pytest.mark.asyncio
async def test_normal_message_does_not_use_schedule_tool() -> None:
    graph = build_graph()
    state = make_state("Hello")

    mock_content = json.dumps(
        {
            "reply": "Hello! How can I help you?",
            "scheduleLookup": None,
        }
    )

    with patch(
        "app.graph.nodes.ChatOllama.invoke",
        return_value=MockResponse(content=mock_content),
    ):
        result = await graph.ainvoke(state)

    assert result["scheduleLookup"] is None
    assert result["tool_result"] is None
    assert result["tool_calls"] == 0
