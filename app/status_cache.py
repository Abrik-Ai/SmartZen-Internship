import time

from app.ollama_status import check_ollama_status

_cached_result: bool | None = None
_last_checked: float | None = None

def get_ollama_status() -> bool:
    global _cached_result, _last_checked
    if _last_checked is None or (time.perf_counter() - _last_checked) > 30:
        _cached_result = check_ollama_status()
        _last_checked = time.perf_counter()
    else: 
        assert _cached_result is not None
        
    return _cached_result