class ToolCallError(Exception):
    """Base class for calling tool errors"""

class ToolTimeout(ToolCallError):
    """Raised when a request times out"""

class ToolUnavailable(ToolCallError):
    """Raised when a backend is down"""

class ToolForbidden(ToolCallError):
    """Raised when a backend returns 403, caller not allowed"""

class ToolNotFound(ToolCallError):
    """Raised when a backend returns 404, resource not found"""

