from dataclasses import dataclass
from unittest.mock import patch

import httpx
import ollama
import pytest

from app.ollama_client import call_ollama
from app.ollama_errors import (
    OllamaClientError,
    OllamaInvalidJSONError,
    OllamaModelNotFoundError,
    OllamaTimeoutError,
    OllamaUnreachableError,
)


@dataclass
class MockResponse:
    content: str

def test_unreachable_request_error() -> None: 
    with patch("app.ollama_client.ChatOllama.invoke", 
               side_effect=httpx.ConnectError("Connection error")):
        with pytest.raises(OllamaUnreachableError):
            call_ollama([("human", "Test prompt")])

def test_timeout_request_error() -> None:
    with patch("app.ollama_client.ChatOllama.invoke", 
               side_effect=httpx.TimeoutException ("Timeout error")):
        with pytest.raises(OllamaTimeoutError):
            call_ollama([("human", "Test prompt")])

def test_model_not_found_error() -> None:
    with patch("app.ollama_client.ChatOllama.invoke", 
               side_effect=ollama.ResponseError("Model not found", status_code=404)):
        with pytest.raises(OllamaModelNotFoundError):
            call_ollama([("human", "Test prompt")])

def test_invalid_json_response() -> None:
    with patch("app.ollama_client.ChatOllama.invoke", 
               return_value=MockResponse(content='{"answer": "undefined"')):
        with pytest.raises(OllamaInvalidJSONError):
            call_ollama([("human", "Test prompt")])

def test_client_error() -> None:
    with patch("app.ollama_client.ChatOllama.invoke", 
               side_effect=Exception("Unexpected error")):
        with pytest.raises(OllamaClientError):
            call_ollama([("human", "Test prompt")])

def test_ollama_response_error_non_404_raises_client_error() -> None:
    with patch(
        "app.ollama_client.ChatOllama.invoke",
        side_effect=ollama.ResponseError("Internal server error", 500),
    ):
        with pytest.raises(OllamaClientError):
            call_ollama([("human", "Test prompt")])
        


    
    



