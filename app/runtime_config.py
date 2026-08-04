"""Lets ops swap the pinned Ollama model with a config change, not a code change.

`get_pinned_model()` is called at request time — never cached in a
module-level constant — so a new value takes effect on the very next
request, no redeploy and no restart needed.

Primary source: an optional small JSON file (path from
SMARTZEN_RUNTIME_CONFIG, defaults to ./runtime_config.json). It's cheap
enough to read on every call, and editing it is exactly the "config change"
the model-swap requirement is asking for. If the file is missing, empty, or
malformed, that's not an error — we just fall back to OLLAMA_MODEL from the
environment (re-read live, not app.config's import-time copy).
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from app.config import OLLAMA_MODEL as _DEFAULT_MODEL

RUNTIME_CONFIG_PATH_ENV = "SMARTZEN_RUNTIME_CONFIG"
DEFAULT_RUNTIME_CONFIG_PATH = "runtime_config.json"


def _config_path() -> Path:
    return Path(os.getenv(RUNTIME_CONFIG_PATH_ENV, DEFAULT_RUNTIME_CONFIG_PATH))


def get_pinned_model() -> str:
    path = _config_path()
    if path.exists():
        try:
            data = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            data = None
        if isinstance(data, dict):
            model = data.get("ollama_model")
            if isinstance(model, str) and model.strip():
                return model.strip()

    # Re-read the env var live rather than trust app.config's value captured
    # at import time, so an env override also takes effect without a restart
    # of anything that re-imports app.config.
    return os.getenv("OLLAMA_MODEL", _DEFAULT_MODEL)
