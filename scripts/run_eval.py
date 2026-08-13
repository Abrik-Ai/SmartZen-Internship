import asyncio
import os
import sys
from typing import Any

from dotenv import load_dotenv

from app.backend_client import BackendClient
from app.evals.load_golden_set import load_golden_set
from app.graph.graph import build_graph
from app.graph.state import GraphState

load_dotenv()  # Load environment variables from .env file

# Set required dummy env vars for evaluation/testing before app imports
os.environ.setdefault("JWT_ACCESS_SECRET", "eval_dummy_secret_1234567890")



client = BackendClient()

async def get_auth_token() -> str:
    email = os.getenv("EVAL_ACCOUNT_EMAIL")
    password = os.getenv("EVAL_ACCOUNT_PASSWORD")

    if not email or not password:
        raise ValueError(
            "EVAL_ACCOUNT_EMAIL and EVAL_ACCOUNT_PASSWORD must be set in the .env"
        )

    result = await client.login(email=email, password=password)
    return result.access_token


def entry_to_graph_state(entry: dict, access_token: str) -> GraphState:
    return {
        "message": entry["message"],
        "caller": entry["role"],
        "history": [],
        "reply": "",
        "token": access_token,  
        "toolCall": None,
        "tool_result": None,
        "tool_calls": 0,
        "loop_count": 0,
        "room_context": None
    }

def get_actual_tool(output_state: dict) -> Any | None:
    tool_call = output_state.get("toolCall")
    if tool_call is not None:
        return tool_call.get("name")
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
    graph = build_graph(client=client)

    entries = load_golden_set("app/evals/data/golden_set.yaml")
    access_token = await get_auth_token()

    total = len(entries)
    tool_correct = 0
    proposal_total = 0
    proposal_correct = 0
    invalid_json_count = 0
    failures = []

    for entry in entries:
        state = entry_to_graph_state(entry, access_token)
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
    report_lines = [
         f"Total:            {total}",
        f"Tool accuracy:    {tool_correct}/{total}  ({tool_pct:.0%})",
        f"Proposal accuracy: {proposal_correct}/{proposal_total}  ({prop_pct:.0%})",
        f"Invalid JSON:     {invalid_json_count}/{total}  ({invalid_pct:.0%})",
        "Failures:",
    ]
    report_lines.extend(failures)  

    tool_accuracy = tool_correct / total if total > 0 else 0.0
    BASELINE_TARGET = 0.82

    if tool_accuracy < BASELINE_TARGET:
        status_line = (
        f" CI Failed: Accuracy ({tool_accuracy:.0%}) "
        f"dropped below threshold ({BASELINE_TARGET:.0%})"
    )
        exit_code = 1
        
    else:
        status_line = " CI Passed: Tool accuracy meets baseline standards!"
        exit_code = 0

    report_text = "\n".join(report_lines) + "\n" + status_line
    print(report_text)

    with open("eval_report.txt", "w") as f:
        f.write(report_text)

    sys.exit(exit_code)


if __name__ == "__main__":
    asyncio.run(run_eval())

