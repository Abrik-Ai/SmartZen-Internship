import json
import logging
from unittest.mock import patch

import pytest
from app.tracing import RunTrace, create_trace


def test_create_trace() -> None:
    trace = create_trace("What is the weather?", "qwen2.5:3b")
    assert trace.run_id is not None
    assert trace.question == "What is the weather?"
    assert trace.model == "qwen2.5:3b"


def test_trace_finish(caplog) -> None:
    with caplog.at_level(logging.INFO):
        trace = create_trace("Hello", "qwen2.5:3b")
        trace.finish(reply="Hi there!", tokens=5, tool="none")
        
        assert trace.reply == "Hi there!"
        assert trace.tokens_used == 5
        assert trace.tool_chosen == "none"
        assert trace.end_time is not None
        
        # Check log output
        assert len(caplog.records) >= 1
        log_entry = json.loads(caplog.records[-1].message)
        assert log_entry["run_id"] == trace.run_id
        assert log_entry["question"] == "Hello"
        assert log_entry["latency_seconds"] >= 0