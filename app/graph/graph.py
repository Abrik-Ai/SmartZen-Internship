from functools import partial

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.backend_client import BackendClient
from app.graph.nodes import ask_model, run_tool
from app.graph.state import GraphState


def should_run_tool(state: GraphState) -> str:
    """Decide whether the graph should execute a tool."""

    if state.get("toolCall") is not None:
        return "tool"

    return END


def build_graph(client: BackendClient) -> CompiledStateGraph:
    """Build the SmartZen LangGraph."""

    graph = StateGraph(GraphState)

    graph.add_node("model", ask_model)
    graph.add_node("tool", partial(run_tool, client=client))

    graph.add_edge(START, "model")

    graph.add_conditional_edges(
        "model",
        should_run_tool,
        {
            "tool": "tool",
            END: END,
        },
    )

    graph.add_edge("tool", END)

    return graph.compile()