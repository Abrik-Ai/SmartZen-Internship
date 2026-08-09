"""Ollama warm-up and keep-alive service.

Ensures the model is pre-pulled on startup and kept warm with periodic
keep-alive requests to avoid cold start latency on the first real request.
"""

import asyncio
import logging

import httpx
import ollama

from app.config import OLLAMA_BASE_URL, OLLAMA_MODEL

logger = logging.getLogger(__name__)

KEEP_ALIVE_INTERVAL_SECONDS = 30.0


async def pull_model_if_missing() -> None:
    """Pull the model if it's not already available."""
    try:
        client = ollama.AsyncClient(host=OLLAMA_BASE_URL, timeout=10.0)
        response = await client.list()
        model_names = [m.model for m in response.models]
        
        if OLLAMA_MODEL not in model_names:
            logger.info(f"Model '{OLLAMA_MODEL}' not found. Pulling...")
            await client.pull(model=OLLAMA_MODEL)
            logger.info(f"Model '{OLLAMA_MODEL}' pulled successfully.")
        else:
            logger.info(f"Model '{OLLAMA_MODEL}' already available.")
    except Exception as e:
        logger.warning(f"Could not pull model on startup: {e}")


async def keep_alive_loop() -> None:
    """Send periodic keep-alive requests to keep the model warm."""
    while True:
        try:
            # Send a minimal ping request to keep the model loaded
            client = ollama.AsyncClient(host=OLLAMA_BASE_URL, timeout=5.0)
            await client.chat(
                model=OLLAMA_MODEL,
                messages=[{"role": "user", "content": "ping"}],
                stream=False,
            )
            logger.debug("Keep-alive ping successful.")
        except Exception as e:
            logger.warning(f"Keep-alive ping failed: {e}")
        
        await asyncio.sleep(KEEP_ALIVE_INTERVAL_SECONDS)


async def start_warmup() -> None:
    """Start the warm-up and keep-alive process."""
    await pull_model_if_missing()
    asyncio.create_task(keep_alive_loop())