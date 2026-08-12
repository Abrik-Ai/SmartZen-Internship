"""Run tracing for chat requests.

Structured logs per request that capture:
- User question
- Which tool was chosen (if any)
- Tokens used
- Latency
- Whether the output was valid JSON
- Final response
"""

import json
import logging
import time
import uuid
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class RunTrace:
    """Structured trace for a single chat run."""
    run_id: str
    question: str
    model: str
    start_time: float = field(default_factory=time.time)
    end_time: float | None = None
    tokens: int | None = None
    tool_chosen: str | None = None
    is_valid_json: bool | None = None
    reply: str | None = None
    error: str | None = None

    def finish(self, reply: str, tokens: int | None = None, 
               tool: str | None = None, is_valid_json: bool = True,
               error: str | None = None) -> None:
        """Complete the trace with results."""
        self.end_time = time.time()
        self.reply = reply
        self.tokens = tokens
        self.tool_chosen = tool
        self.is_valid_json = is_valid_json
        self.error = error
        self._log()

    def _log(self) -> None:
        """Log the complete trace as a structured JSON line."""
        latency = (self.end_time or time.time()) - self.start_time
        log_entry = {
            "run_id": self.run_id,
            "question": self.question,
            "model": self.model,
            "latency_seconds": round(latency, 3),
            "tokens": self.tokens,
            "tool_chosen": self.tool_chosen,
            "is_valid_json": self.is_valid_json,
            "reply_preview": self.reply[:200] if self.reply else None,
            "error": self.error,
        }
        logger.info(json.dumps(log_entry))


def create_trace(question: str, model: str) -> RunTrace:
    """Create a new run trace."""
    return RunTrace(
        run_id=str(uuid.uuid4()),
        question=question,
        model=model,
    )