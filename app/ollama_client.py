import json  #for parsing Ollama's response to a Python dict

import httpx  #to catch ConnectError, TimeoutException
import ollama  #to catch ResponseError (Error 404)
from langchain_ollama import ChatOllama

from app.config import OLLAMA_BASE_URL, OLLAMA_MODEL
from app.ollama_errors import (
    OllamaClientError,
    OllamaInvalidJSONError,
    OllamaModelNotFoundError,
    OllamaTimeoutError,
    OllamaUnreachableError,
)

print("langchain_ollama imported OK")

EXAMPLE_SCHEMA = {
    "type": "object",
    "properties": {
          "answer": {"type": "string"},
        },
    "required": ["answer"], 
}


def call_ollama(messages: list[tuple[str, str]]) -> dict:
    client = ChatOllama(
        model=OLLAMA_MODEL, 
        base_url=OLLAMA_BASE_URL, 
        format=EXAMPLE_SCHEMA, 
        temperature=0.4,
        client_kwargs={"timeout": 30}
        #Explicit timeout to avoid indefinitely request
        )
    


    
    try:
        response = client.invoke(messages)
    except httpx.ConnectError as e:
        raise OllamaUnreachableError(f"Could not connect to Ollama at {OLLAMA_BASE_URL}") from e
    except httpx.TimeoutException as e:
        raise OllamaTimeoutError("Request to Ollama timed out") from e
    except ollama.ResponseError as e:
        if e.status_code == 404:
            raise OllamaModelNotFoundError(
                f"Model '{OLLAMA_MODEL}' not found — run 'ollama pull {OLLAMA_MODEL}'"
            ) from e
        raise OllamaClientError(f"Ollama returned an error: {e}") from e
    except Exception as e:
        raise OllamaClientError(f"Unexpected error calling Ollama: {e}") from e

    try:
        content = response.content
        #LangChaine types .contents as str | list[]
        #Ollama returns plaint text
        #explicltly asserting is needed to avoid mypy error
        assert isinstance(content, str)
        parsed: dict = json.loads(content)
        return parsed
    except json.JSONDecodeError as e:
        raise OllamaInvalidJSONError(f"Response was not valid JSON: {response.content!r}") from e

if __name__ == "__main__":
    result = call_ollama([("human", "What is the capital of Cyprus?")])
    print(result)