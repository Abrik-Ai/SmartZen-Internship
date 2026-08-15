"""Tests the exception hierarchy and subtyping behavior for `app.tool_errors`.
Nothing under app/ catches any of these five exceptions 
— not the base, not the specific types. 
Test ensures that all custom tool exceptions correctly inherit from `ToolCallError` 
and standard Python `Exception`, retain custom error messages, and remain 
strictly isolated from sibling exception classes. 
"""

from itertools import permutations

import pytest

from app.tool_errors import ToolCallError, ToolForbidden, ToolNotFound, ToolTimeout, ToolUnavailable

SUBCLASSES: list[type[ToolCallError]] = [
    ToolTimeout,
    ToolUnavailable,
    ToolForbidden,
    ToolNotFound
]

ALL_ERRORS: list[type[ToolCallError]] = [
     ToolCallError,
     ToolTimeout,
     ToolUnavailable,
     ToolForbidden,
     ToolNotFound   
]

@pytest.mark.parametrize("exc_class", SUBCLASSES)
def test_inherits_from_call_error(exc_class: type[ToolCallError]) -> None:
    assert issubclass(exc_class, ToolCallError)

def test_call_error_inherits_from_exception() -> None:
    assert issubclass(ToolCallError, Exception)

@pytest.mark.parametrize("exc_class", SUBCLASSES)
def test_catchable_as_base(exc_class: type[ToolCallError]) -> None:
    with pytest.raises(ToolCallError):
        raise exc_class()

@pytest.mark.parametrize("exc_class", ALL_ERRORS)
def test_catchable_as_own_type(exc_class: type[ToolCallError]) -> None:
    with pytest.raises(exc_class):
        raise exc_class()

@pytest.mark.parametrize("exc_class", ALL_ERRORS)
def test_preserves_custom_message(exc_class: type[ToolCallError]) -> None:
    message = "Error happened while processing the request"
    exc = exc_class(message)
    assert str(exc) == message 

@pytest.mark.parametrize("child, parent", list(permutations(SUBCLASSES, 2)))
def test_siblings_not_subclasses(child: type[ToolCallError],
                                 parent: type[ToolCallError]) -> None:
    assert not issubclass(child, parent)