import json
import logging
from typing import Any

from langchain_ollama import ChatOllama

from app.config import OLLAMA_BASE_URL, OLLAMA_MODEL
from app.graph.state import GraphState
from app.models.graph_models import GraphResponse
from app.ollama_client import OllamaClientError, OllamaInvalidJSONError
from app.tools.schedule_stub import schedule_lookup_stub

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """
You are the SmartZen AI assistant.

You must respond with ONLY valid JSON matching this exact flat schema:

{
  "reply": "string",
  "scheduleLookup": {"range": "today" | "week" | "upcoming"} | null
}

Rules:
- reply is always required.
- scheduleLookup must be null unless the user is asking about a schedule.
- If the user asks about a schedule, set scheduleLookup to exactly one object.
- Never create more than one scheduleLookup.
- Do not add any other JSON fields.
- Do not use markdown.

Examples:

User: What's my schedule today?

{
  "reply": "I'll check your schedule for today.",
  "scheduleLookup": {"range": "today"}
}

User: Hello

{
  "reply": "Hello! How can I help you?",
  "scheduleLookup": null
}
"""


def build_prompt(state: GraphState) -> list[tuple[str, str]]:
    """Build the conversation sent to the model."""

    messages: list[tuple[str, str]] = [
        ("system", SYSTEM_PROMPT)
    ]

    for item in state.get("history", []):
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
        format={
            "type": "object",
            "properties": {
                "reply": {
                    "type": "string",
                },
                "scheduleLookup": {
                    "anyOf": [
                        {
                            "type": "object",
                            "properties": {
                                "range": {
                                    "type": "string",
                                    "enum": [
                                        "today",
                                        "week",
                                        "upcoming",
                                    ],
                                }
                            },
                            "required": ["range"],
                            "additionalProperties": False,
                        },
                        {
                            "type": "null",
                        },
                    ],
                },
            },
            "required": ["reply", "scheduleLookup"],
            "additionalProperties": False,
        },
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

        schedule_lookup = (
            validated.scheduleLookup.model_dump()
            if validated.scheduleLookup is not None
            else None
        )

        return {
            "reply": validated.reply,
            "scheduleLookup": schedule_lookup,
        }

    except (
        json.JSONDecodeError,
        ValueError,
        OllamaInvalidJSONError,
    ) as exc:
        logger.warning("Model returned invalid JSON: %s", exc)

        return {
            "reply": "Sorry, I couldn't process that request.",
            "scheduleLookup": None,
        }

    except OllamaClientError as exc:
        logger.exception("Ollama request failed: %s", exc)

        return {
            "reply": "Sorry, I couldn't process that request.",
            "scheduleLookup": None,
        }


async def run_tool(state: GraphState) -> dict[str, Any]:
    """Run the selected tool when scheduleLookup is present."""

    schedule_lookup = state.get("scheduleLookup")

    if schedule_lookup is None:
        return {
            "tool_result": None,
            "tool_calls": state.get("tool_calls", 0),
        }

    range_value = schedule_lookup["range"]

    result = await schedule_lookup_stub(range_value)

    return {
        "tool_result": result,
        "tool_calls": state.get("tool_calls", 0) + 1,
    }