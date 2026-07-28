import time
from collections.abc import Callable

import httpx

from app.tool_errors import ToolCallError, ToolForbidden, ToolNotFound, ToolTimeout, ToolUnavailable


def call_with_retries(request_func: Callable[[], httpx.Response]) -> httpx.Response:
    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            response = request_func()
            response.raise_for_status()
            return response
        except httpx.ConnectError as e:
            if attempt == max_retries:
                raise ToolUnavailable(f"Could not connect to the tool:{e}") from e
            time.sleep(2 ** attempt)
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            if status_code == 403:
                raise ToolForbidden("Caller is not allowed") from e
            elif status_code == 404:
                raise ToolNotFound("Resourse is not found") from e
            elif status_code >= 500:
                if attempt == max_retries:
                     raise ToolUnavailable(f"Backend returned {status_code}") from e
                time.sleep(2 ** attempt)
            else:
                raise ToolCallError("Error happened while processing the request") from e
        except httpx.TimeoutException as e:
            if attempt == max_retries:
                raise ToolTimeout("Request timed out") from e
            time.sleep(2 ** attempt)
    raise ToolCallError("Retries exhausted") #mypy satisfies that this line is unreachable 
            