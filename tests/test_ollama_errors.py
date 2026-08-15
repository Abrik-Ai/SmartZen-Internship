""" This file tests the exception hierarchy in app.ollama_errors, 
not the client that raises it. `main.py` and `nodes.py` catch OllamaClientError so that 
any Ollama failure becomes a safe response instead of a 500. 
That only works while every error in this module
inherits from that base and none of them inherit from each other.
"""

from itertools import permutations

import pytest

from app.ollama_errors import (
    OllamaClientError,
    OllamaInvalidJSONError,
    OllamaModelNotFoundError,
    OllamaTimeoutError,
    OllamaUnreachableError,
)

SUBCLASSES: list[type[OllamaClientError]] = [OllamaUnreachableError,
                                             OllamaModelNotFoundError,
                                             OllamaTimeoutError,
                                             OllamaInvalidJSONError]

ALL_ERRORS: list[type[OllamaClientError]] = [OllamaClientError,
                                     OllamaUnreachableError,
                                     OllamaModelNotFoundError,
                                     OllamaTimeoutError,
                                     OllamaInvalidJSONError]

@pytest.mark.parametrize("exc_class", SUBCLASSES)
def test_inherits_from_client_error(exc_class: type[OllamaClientError]) -> None:
    assert issubclass(exc_class, OllamaClientError)

def test_client_error_inherits_from_exception() -> None:
    assert issubclass(OllamaClientError, Exception)

@pytest.mark.parametrize("exc_class", SUBCLASSES)
def test_catchable_as_base(exc_class: type[OllamaClientError]) -> None:
    with pytest.raises(OllamaClientError):
        raise exc_class()

@pytest.mark.parametrize("exc_class", SUBCLASSES)
def test_catchable_as_own_type(exc_class: type[OllamaClientError]) -> None:
    with pytest.raises(exc_class):
        raise exc_class()

@pytest.mark.parametrize("exc_class", ALL_ERRORS)
def test_preserves_custom_message(exc_class: type[OllamaClientError]) -> None:
    exc = exc_class("request took 12s")
    assert str(exc) == "request took 12s"

@pytest.mark.parametrize("child, parent", list(permutations(SUBCLASSES, 2)))
def test_siblings_not_subclasses(child: type[OllamaClientError],
                                 parent: type[OllamaClientError]) -> None:
    assert not issubclass(child, parent)