import asyncio
import sys

from app.evals.load_golden_set import load_golden_set
from app.graph.graph import build_graph
from app.graph.state import GraphState


def entry_to_graph_state(entry: dict) -> GraphState:
    return {
        "message": entry["message"],
        "caller": entry["role"],
        "history": [],
        "reply": "",
        "scheduleLookup": None,
        "tool_result": None,
        "tool_calls": 0,
        "loop_count": 0,
    }

def get_actual_tool(output_state: dict) -> str | None:
    if output_state.get("scheduleLookup") is not None:
        return "scheduleLookup"
    return None

def get_actual_proposal(output_state: dict) -> dict | None:
    tool_result = output_state.get("tool_result")
    if tool_result is None or len(tool_result) == 0:
        return None
    
    if isinstance(tool_result, list):
        return tool_result[0] if len(tool_result) > 0 else None

    if isinstance(tool_result, dict):
        return tool_result

    return None

async def run_eval() -> None:
    graph = build_graph()

    entries = load_golden_set("app/evals/data/golden_set.yaml")

    total = len(entries)
    tool_correct = 0
    proposal_total = 0
    proposal_correct = 0
    invalid_json_count = 0
    failures = []

    for entry in entries:
        state = entry_to_graph_state(entry)
        output_state = await graph.ainvoke(state)

        expected_tool = entry.get("expect_tool")
        actual_tool = get_actual_tool(output_state)
        if actual_tool == expected_tool:
            tool_correct += 1
        else: 
            exp_str = expected_tool if expected_tool else "null"
            act_str = actual_tool if actual_tool else "null"
            failures.append(
                f"  {entry.get('id', 'unknown')}\texpected {exp_str}, got {act_str}"
            )

        expected_proposal = entry.get("expect_proposal")
        if expected_proposal is not None:
            proposal_total += 1
            actual_proposal = get_actual_proposal(output_state)
            if actual_proposal == expected_proposal:
                proposal_correct += 1

        if "Sorry, I couldn't process that request." in output_state.get(
            "reply", ""
        ):
            invalid_json_count += 1

        tool_pct = tool_correct / total if total > 0 else 0.0
        prop_pct = proposal_correct / proposal_total if proposal_total > 0 else 0.0
        invalid_pct = invalid_json_count / total if total > 0 else 0.0

        print(f"Total:            {total}")
        print(f"Tool accuracy:    {tool_correct}/{total}  ({tool_pct:.0%})")
        print(f"Proposal accuracy: {proposal_correct}/{proposal_total}  ({prop_pct:.0%})")
        print(f"Invalid JSON:     {invalid_json_count}/{total}  ({invalid_pct:.0%})")
        print("Failures:")
            
    for failure in failures:
        print(failure)

    tool_accuracy = tool_correct / total if total > 0 else 0.0
    BASELINE_TARGET = 0.82
    if tool_accuracy < BASELINE_TARGET:
        print(f" CI Failed: Accuracy ({tool_accuracy:.0%}) "
              f"dropped below threshold ({BASELINE_TARGET:.0%})")
        sys.exit(1)
    else:
        print(" CI Passed: Tool accuracy meets baseline standards!")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(run_eval())

