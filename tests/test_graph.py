import json
from dataclasses import dataclass
from unittest.mock import patch

import pytest

from app.backend_client import BackendClient
from app.graph.graph import build_graph
from app.graph.state import GraphState


@dataclass
class MockResponse:
    content: str


client = BackendClient()


def make_state(message: str) -> GraphState:
    return {
        "message": message,
        "history": [],
        "caller": "INSTRUCTOR",
        "reply": "",
        "token": "mock-token-123",
        "toolCall": None,
        "tool_result": None,
        "tool_name": None,
        "tool_calls": 0,
        "loop_count": 0,
        "room_context": None
    }


@pytest.mark.asyncio
async def test_schedule_today_uses_schedule_tool() -> None:
    graph = build_graph(client=client)
    state = make_state("What's my schedule today?")

    mock_content = json.dumps(
        {
            "reply": "I'll check your schedule for today.",
            "toolCall": {
                "name": "get_my_schedule",
                "args": {"range_value": "today"},
            },
        }
    )

    with patch(
        "app.graph.nodes.ChatOllama.invoke",
        return_value=MockResponse(content=mock_content),
    ):
        with patch(
            "app.graph.nodes.get_my_schedule",
            return_value=[
                {
                    "id": "sched-1",
                    "course_label": "Physics 101",
                    "start_time": "2026-08-11T14:00:00Z",
                    "end_time": "2026-08-11T15:00:00Z",
                    "room": {"id": "ST101", "name": "ST101", "building": "ST"},
                }
            ],
        ):
            result = await graph.ainvoke(state)

    assert result["toolCall"] == {
        "name": "get_my_schedule",
        "args": {"range_value": "today"},
    }
    assert result["tool_result"] == [
        {
            "id": "sched-1",
            "course_label": "Physics 101",
            "start_time": "2026-08-11T14:00:00Z",
            "end_time": "2026-08-11T15:00:00Z",
            "room": {"id": "ST101", "name": "ST101", "building": "ST"},
        }
    ]
    assert result["tool_calls"] == 1


@pytest.mark.asyncio
async def test_room_request_uses_room_tool() -> None:
    graph = build_graph(client=client)
    state = make_state("Find me a room for 30 minutes")

    mock_content = json.dumps(
        {
            "reply": "Looking for available rooms.",
            "toolCall": {
                "name": "find_free_rooms",
                "args": {"minutes_needed": 30, "start_time": None},
            },
        }
    )

    with patch(
        "app.graph.nodes.ChatOllama.invoke",
        return_value=MockResponse(content=mock_content),
    ):
        with patch(
            "app.graph.nodes.find_free_rooms",
            return_value=[
                {
                    "id": "CU201",
                    "name": "CU201",
                    "building": "CU",
                    "type": "classroom",
                    "next_class": {
                        "start_time": "2026-08-11T15:00:00Z",
                        "course_label": "Algorithms",
                    },
                }
            ],
        ):
            result = await graph.ainvoke(state)

    assert result["toolCall"] == {
        "name": "find_free_rooms",
        "args": {"minutes_needed": 30, "start_time": None},
    }
    assert result["tool_result"] == [
        {
            "id": "CU201",
            "name": "CU201",
            "building": "CU",
            "type": "classroom",
            "next_class": {
                "start_time": "2026-08-11T15:00:00Z",
                "course_label": "Algorithms",
            },
        }
    ]
    assert result["tool_calls"] == 1


@pytest.mark.asyncio
async def test_normal_message_does_not_use_tool() -> None:
    graph = build_graph(client=client)
    state = make_state("Hello")

    mock_content = json.dumps(
        {
            "reply": "Hello! How can I help you?",
            "toolCall": None,
        }
    )

    with patch(
        "app.graph.nodes.ChatOllama.invoke",
        return_value=MockResponse(content=mock_content),
    ):
        result = await graph.ainvoke(state)

    assert result["toolCall"] is None
    assert result["tool_result"] is None
    assert result["tool_calls"] == 0
