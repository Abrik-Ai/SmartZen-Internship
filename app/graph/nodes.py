import json
import logging
from typing import Any

from langchain_ollama import ChatOllama
from pydantic import BaseModel

from app.backend_client import BackendClient
from app.config import OLLAMA_BASE_URL, OLLAMA_MODEL
from app.graph.role_context import get_role_context
from app.graph.state import GraphState
from app.models.graph_models import GraphResponse
from app.ollama_client import OllamaClientError, OllamaInvalidJSONError
from app.tool_errors import ToolCallError
from app.tools import (
    RoomContext,
    documentation_search,
    find_free_rooms,
    get_my_schedule,
    get_room_context,
    get_room_status,
)

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """
You are the SmartZen AI assistant.

You must respond with ONLY valid JSON matching this exact schema:

{
  "reply": "string",
  "toolCall": {
        "name": "get_my_schedule" | "find_free_rooms" | "get_room_status" | "documentation_search",
        "args": { ... }
  } | {
        "name": "find_free_rooms",
        "args": { "minutes_needed": int, "start_time": string | null }
    } | {
        "name": "get_room_status",
        "args": {}
    } | {
        "name": "documentation_search",
        "args": { "query": string }
  } | null
}

## Role & Global Rules
You are a university assistant. Answer queries using the appropriate tool 
    ONLY when an exact match exists.
1. **NO TOOL RULE:** If a user request cannot be fulfilled by the tools below 
    (e.g., room booking/locking,physical actions, asking what services you offer), 
    DO NOT call any tool. Respond directly in natural text.
2. **USER RESPONSE RULE:** Never mention internal technical terms, function names, parameter names, 
    or the word "tool" in your replies to the user.

---

# Available Tools

### 1. `find_free_rooms`
* **Purpose:** Search for available rooms by duration.
* **When to use:** User asks to find an open/free room without naming a specific room.
* **DO NOT USE:** Do NOT call if the user asks about a specific room name/ID 
    (e.g., "Is CU101 free?").
* **Parameters:**
  * `minutes_needed` (integer, required): Duration in minutes. 
  If unspecified by user, default to `60`. Convert hours to minutes.
  * `start_time` (string, optional): ISO 8601 start time string.

### 2. `get_room_status`
* **Purpose:** Fetch the user's active session and current room telemetry.
* **When to use:** User asks about their current active room or session state.
* **DO NOT USE:** Takes no room ID argument; do NOT call to query 
    arbitrary room IDs or perform bookings.
* **Parameters:** None.

### 3. `get_my_schedule`
* **Purpose:** Fetch the user's personal timetable.
* **When to use:** User asks for their personal class/exam schedule.
* **Parameters:**
  * `range_value` (string, required): MUST be exactly one of: `"today"`, `"week"`, or `"upcoming"`.

### 4. `documentation_search`
* **Purpose:** Search general university documentation and policies.
* **When to use:** User asks "how-to" questions, policy questions, or static feature explanations.
* **DO NOT USE:** Do NOT call for user-specific dynamic data 
    (schedules, active sessions, available rooms).
* **Parameters:**
  * `query` (string, required): Search keywords.

Examples:

User: What's my schedule today?
{
  "reply": "Checking your schedule for today...",
  "toolCall": {
    "name": "get_my_schedule",
        "args": {"range_value": "today"}
  }
}

User: Find me a room for 30 minutes
{
  "reply": "Looking for available rooms...",
  "toolCall": {
    "name": "find_free_rooms",
    "args": {"minutes_needed": 30, "start_time": null}
  }
}

User: Hello
{
  "reply": "Hello! How can I help you?",
  "toolCall": null
}

User: is room CU101 free right now
{
  "reply": "I can't check a specific room, but I can find an available room for you 
    instead.",
  "toolCall": null
}
"""

def _format_room_context(room_context: RoomContext) -> str:
    """Format live room and sensor data for the model prompt."""
    summary = (f"The caller is currently in room {room_context.room_name}, "
        f"teaching {room_context.current_class}, which ends at "
        f"{room_context.end_time.strftime('%H:%M')}, "
        f"({room_context.minutes_left} minutes from now.)"
    )

    sensors: list[str] = []
    if room_context.readings.temperature is not None:
        sensors.append(f"The temperature is {room_context.readings.temperature}°C.")
    if room_context.readings.humidity is not None:
        sensors.append(f"Humidity is {room_context.readings.humidity}%.")
    if room_context.readings.co2 is not None:
        sensors.append(f"CO2 is {room_context.readings.co2} ppm.")
    if room_context.readings.lux is not None:
        sensors.append(f"The light level is {room_context.readings.lux} lux.")
    if room_context.readings.presence is not None:
        if room_context.readings.presence: 
            sensors.append("The room is occupied.")
        else:
            sensors.append("The room is empty.")
    if room_context.readings.window_open is not None:
        if room_context.readings.window_open:
            sensors.append("The window is open.")
        else:
            sensors.append("The window is closed.")
    if not sensors:
        return summary
    return summary + " " + " ".join(sensors) 

# Cap on how many history entries reach the model
MAX_HISTORY_ENTRIES = 8

# Approximate characters-per-token for English prose (~4:1 for ordinary
# text)
# A real tokenizer was considered and rejected: it would mean adding
# transformers as a *production* dependency, downloading or vendoring
# Qwen tokenizer files, and a CI network allowlist change — all to make a
# safety rail precise. It also introduces a silent-drift failure
# mode if the HuggingFace model name ever diverges from OLLAMA_MODEL.
CHARS_PER_TOKEN = 4

# Conservative ceiling for the whole prompt. qwen2.5:3b declares 32768
# 2048 leaves reserve for generation, approximation error, and chat-template overhead.
MAX_PROMPT_TOKENS = 2048

def _history_length(history: list[dict[str, str]]) -> int:
    """Approximate character cost of a history slice."""
    return sum(len(item.get("content", "")) for item in history)

def _trim_history(history: list[dict[str, str]], char_budget: int) -> list[dict[str, str]]:
    """Reduce history to what should actually be sent to the model."""
    trimmed = history[-MAX_HISTORY_ENTRIES:]

    if trimmed and trimmed[0].get("role") == "assistant":
        trimmed = trimmed[1:]

    # `> 1` not `> 0`: the check runs before the drop, so it must leave one entry standing.
    while len(trimmed) > 1 and _history_length(trimmed) > char_budget:
        trimmed = trimmed[1:]
        if len(trimmed) > 1  and trimmed[0].get("role") == "assistant":
            trimmed = trimmed[1:]

    return trimmed




def build_prompt(state: GraphState) -> list[tuple[str, str]]:
    """Build the conversation sent to the model."""

    messages: list[tuple[str, str]] = [
        ("system", SYSTEM_PROMPT)
    ]

    role_context = get_role_context(state["caller"])

    if role_context:
        messages.append(("system", role_context))

    room_context = state["room_context"]
    
    if room_context:
        messages.append(("system", _format_room_context(room_context)))

    committed = sum(len(content) for _, content in messages)
    committed += len(state["message"])
    char_budget = MAX_PROMPT_TOKENS * CHARS_PER_TOKEN - committed

    for item in _trim_history(state.get("history", []), char_budget):
        role = item.get("role", "user")
        content = item.get("content", "")

        if role == "assistant":
            messages.append(("assistant", content))
        else:
            messages.append(("human", content))

    messages.append(("human", state["message"]))

    return messages


def ask_model(state: GraphState) -> dict[str, Any]:
    """Ask Ollama for the constrained flat JSON response."""

    client = ChatOllama(
        model=OLLAMA_MODEL,
        base_url=OLLAMA_BASE_URL,
        format=GraphResponse.model_json_schema(),
        temperature=0,
        client_kwargs={"timeout": 60},
    )

    try:
        response = client.invoke(build_prompt(state))
        content = response.content

        if not isinstance(content, str):
            raise ValueError("Model returned non-string content")

        parsed = json.loads(content)

        validated = GraphResponse.model_validate(parsed)

        return {
            "reply": validated.reply,
            "toolCall": validated.toolCall.model_dump() if validated.toolCall is not None else None,
        }

    except (
        json.JSONDecodeError,
        ValueError,
        OllamaInvalidJSONError,
    ) as exc:
        logger.warning("Model returned invalid JSON: %s", exc)

        return {
            "reply": "Sorry, I couldn't process that request.",
            "toolCall": None,
        }

    except OllamaClientError as exc:
        logger.exception("Ollama request failed: %s", exc)

        return {
            "reply": "Sorry, I couldn't process that request.",
            "toolCall": None,
        }


def _serialize_tool_result(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump()

    if isinstance(value, list):
        return [_serialize_tool_result(item) for item in value]

    if isinstance(value, tuple):
        return [_serialize_tool_result(item) for item in value]

    if isinstance(value, dict):
        return {key: _serialize_tool_result(item) for key, item in value.items()}

    return value


async def run_tool(state: GraphState, client: BackendClient) -> dict[str, Any]:
    """Run the selected tool when toolCall is present."""

    token = state["token"] 
    tool_call = state.get("toolCall")
    current_calls = state.get("tool_calls", 0)

    if tool_call is None:
        return {
            "tool_result": None,
            "tool_calls": current_calls,
        }

    name = tool_call["name"]
    args = tool_call.get("args", {})

    result: Any = None

    try:
        match name:
            case "get_my_schedule":
                result = await get_my_schedule(token=token, client=client, **args)
            case "find_free_rooms":
                result = await find_free_rooms(token=token, client=client, **args)
            case "get_room_status":
                result = await get_room_status(token=token, client=client, **args)
            case "documentation_search":
                result = documentation_search(**args)
            case _:
                result = {"error": f"Unknown tool: {name}"}
    except ToolCallError as exc:
        logger.warning(f"Tool call failed for {name}: {exc}")
        result = {"error": str(exc)}
    except Exception as exc:
        logger.exception(f"Unexpected error in tool call for {name}: {exc}")
        result = {"error": str(exc)}

    return {
        "tool_result": _serialize_tool_result(result),
        "tool_calls": current_calls + 1,
    }

async def fetch_room_context(state: GraphState, client: BackendClient) -> dict[str, Any]:
    """Fetch the room context for the current user"""
    
    token = state["token"]
    try:
        room_context = await get_room_context(token=token, client=client)
    except ToolCallError as exc:
        room_context = None
        logger.warning(f"Failed to fetch room context: {exc}")
    except Exception as exc:
        room_context = None
        logger.exception(f"Unexpected error while fetching room context: {exc}")
    return {
        "room_context": room_context
    }