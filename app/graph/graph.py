from functools import partial

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.backend_client import BackendClient
from app.graph.nodes import ask_model, fetch_room_context, run_tool
from app.graph.state import GraphState


def should_run_tool(state: GraphState) -> str:
    """Decide whether the graph should execute a tool."""

    if state.get("toolCall") is not None:
        return "tool"

    return END

# Each loop iteration is a full Ollama round-trip. 3 allows a tool call,
# a second pass to answer from it, and one retry, without letting a
# confused model burn the eval run.
MAX_TOOL_CALLS = 3


def should_continue_after_tool(state: GraphState) -> str:
    """Decide whether the model gets another pass after a tool ran."""

    if state.get("tool_calls", 0) >= MAX_TOOL_CALLS:
        return END

    return "model"


def build_graph(client: BackendClient) -> CompiledStateGraph:
    """Build the SmartZen LangGraph."""

    graph = StateGraph(GraphState)

    graph.add_node("model", ask_model)
    #LangGraph calls nodes with state only, but run_tool also needs a client 
    #partial binds it in advance.
    graph.add_node("tool", partial(run_tool, client=client))

    graph.add_node("room_context", partial(fetch_room_context, client=client))
    graph.add_edge(START, "room_context")
    graph.add_edge("room_context", "model")

    graph.add_conditional_edges(
        "model",
        should_run_tool,
        {
            "tool": "tool",
            END: END,
        },
    )

    graph.add_conditional_edges(
        "tool",
        should_continue_after_tool,
        {
            "model": "model",
            END: END,
        },
    )

    return graph.compile()