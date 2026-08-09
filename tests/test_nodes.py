from dataclasses import dataclass
from unittest.mock import patch

from app.graph.nodes import ask_model
from app.graph.state import GraphState
from tests.test_graph import make_state


@dataclass
class MockResponse:
    content: str 

invalid_json_types: list[str] = [
    '{"reply": "some reply", "scheduleLookup": "today"}',
    '{"scheduleLookup": {"range": "today"}}',
    '{"reply": "some reply',
    "",
]

def test_ask_model_invalid_response() -> None:
    with patch(
        "app.graph.nodes.ChatOllama.invoke",
        return_value=MockResponse(content="NOT_VALID_JSON"),
    ):
        state: GraphState = make_state("test")
        result = ask_model(state)

        assert result["reply"] == "Sorry, I couldn't process that request."
        assert result["scheduleLookup"] is None

def test_hallucinated_response() -> None:
    with patch(
        "app.graph.nodes.ChatOllama.invoke",
        return_value=MockResponse(
            content='{"reply": "some reply", "scheduleLookup": {"range": "yesterday"}}'
            ),
    ):
        state: GraphState = make_state("test")
        result = ask_model(state)

        assert result["reply"] == "Sorry, I couldn't process that request."
        assert result["scheduleLookup"] is None

def test_invalid_json_type() -> None:
    for i in range(100):
        with patch(
            "app.graph.nodes.ChatOllama.invoke",
            return_value=MockResponse(content=invalid_json_types[i % len(invalid_json_types)]),
        ):
            state: GraphState = make_state("test")
            result = ask_model(state)

            assert result["reply"] == "Sorry, I couldn't process that request."
            assert result["scheduleLookup"] is None

            
            