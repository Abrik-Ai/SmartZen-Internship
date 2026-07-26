class OllamaClientError(Exception):
    """Base class for Ollama client errors"""


class OllamaUnreachableError(OllamaClientError):
    """Raised when the Ollama server is unreachable"""


class OllamaModelNotFoundError(OllamaClientError):
    """Raised when Ollama returns 404 - model not found"""


class OllamaTimeoutError(OllamaClientError):
    """Raised when Ollama request times takes too long"""

class OllamaInvalidJSONError(OllamaClientError):
    """Raised when Ollama returns invalid JSON response"""

    
