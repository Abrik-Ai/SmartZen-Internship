import json
import os
import time
from collections.abc import AsyncIterator, Mapping

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from app.assistant_status import is_assistant_enabled
from app.chat_stream import ChatStreamError, stream_chat_tokens
from app.config import OLLAMA_BASE_URL
from app.graph.graph import build_graph
from app.metrics import get_metrics_snapshot, queue_depth_tracker, record_latency
from app.rate_limit import rate_limit
from app.runtime_config import get_pinned_model

app = FastAPI(title="smartzen-ai")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")],
    allow_methods=["*"],
    allow_headers=["*"],
)

_graph = build_graph()

# The one body every failure mode collapses to — Ollama down, model missing,
# queue full, timeout. Deliberately doesn't say *which* one: the client only
# ever needs to know "not available right now", and not distinguishing modes
# avoids leaking backend state to the caller.
DISABLED_RESPONSE_BODY: dict[str, object] = {"enabled": False}

MAX_CONCURRENT_STREAMS = int(os.getenv("ASSISTANT_MAX_CONCURRENT_STREAMS", "5"))


@app.middleware("http")
async def observability_middleware(request: Request, call_next):  # type: ignore[no-untyped-def]
    """Times every request per route, and is the last-resort net that turns
    an unexpected exception on an /assistant/* route into the standard
    disabled response instead of a 500.

    Can't help once a StreamingResponse has already sent headers/bytes —
    that's handled inside chat_stream's own try/except instead.
    """
    start = time.monotonic()
    try:
        response = await call_next(request)
    except Exception:
        record_latency(request.url.path, time.monotonic() - start)
        if request.url.path.startswith("/assistant"):
            return JSONResponse(DISABLED_RESPONSE_BODY, status_code=200)
        raise
    record_latency(request.url.path, time.monotonic() - start)
    return response


@app.get("/health")
def health() -> dict[str, bool]:
    return {"ok": True}


@app.get("/assistant/status")
async def assistant_status(_rate_limited: None = Depends(rate_limit)) -> dict[str, bool]:
    return {"enabled": await is_assistant_enabled()}


@app.get("/assistant/metrics")
async def assistant_metrics(_rate_limited: None = Depends(rate_limit)) -> dict[str, object]:
    return get_metrics_snapshot()


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]


def _sse(event: str, data: Mapping[str, object]) -> bytes:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n".encode()


@app.post("/assistant/chat/stream", response_model=None)
async def chat_stream(
    payload: ChatRequest,
    request: Request,
    _rate_limited: None = Depends(rate_limit),
) -> StreamingResponse | JSONResponse:
    # Pre-flight checks: anything caught here means we never open the stream
    # at all, so a plain JSON body (never a 500) is still on the table.
    if not await is_assistant_enabled():
        return JSONResponse(DISABLED_RESPONSE_BODY)

    if queue_depth_tracker.depth >= MAX_CONCURRENT_STREAMS:
        return JSONResponse(DISABLED_RESPONSE_BODY)

    async def event_source() -> AsyncIterator[bytes]:
        # Once we're here, headers are about to be sent — any failure from
        # this point on has to end the stream with a terminal "disabled"
        # frame, since we can no longer swap in a plain JSON response.
        with queue_depth_tracker.slot():
            try:
                async for token in stream_chat_tokens(
                    messages=[m.model_dump() for m in payload.messages],
                    base_url=OLLAMA_BASE_URL,
                    model=get_pinned_model(),
                    is_disconnected=request.is_disconnected,
                ):
                    yield _sse("token", {"token": token})
                yield _sse("done", {})
            except ChatStreamError:
                yield _sse("disabled", DISABLED_RESPONSE_BODY)

    return StreamingResponse(event_source(), media_type="text/event-stream")


class GraphChatMessage(BaseModel):
    role: str
    content: str


class GraphChatRequest(BaseModel):
    message: str
    history: list[GraphChatMessage] = []


@app.post("/assistant/chat")
async def chat(
    payload: GraphChatRequest,
    request: Request,
    _rate_limited: None = Depends(rate_limit),
) -> dict[str, object]:
    """Runs the tool-calling graph for one turn: the model decides on a reply
    and, if the user asked about their schedule, which tool to call — see
    app/graph/graph.py. Unlike /assistant/chat/stream (a raw passthrough to
    Ollama), this is the endpoint the frontend's assistant panel actually
    talks to.
    """
    if not await is_assistant_enabled():
        return DISABLED_RESPONSE_BODY

    result = await _graph.ainvoke(
        {
            "message": payload.message,
            "history": [m.model_dump() for m in payload.history],
            "caller": request.state.auth.role,
            "reply": "",
            "scheduleLookup": None,
            "tool_result": None,
            "tool_calls": 0,
            "loop_count": 0,
        }
    )

    return {
        "reply": result["reply"],
        "schedules": result.get("tool_result"),
    }


@app.on_event("startup")
async def startup_event() -> None:
    """Start the Ollama warm-up and keep-alive process."""
    from app.ollama_warmup import start_warmup
    await start_warmup()
