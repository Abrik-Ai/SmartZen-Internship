import time
from dataclasses import dataclass

from fastapi import Depends, HTTPException

from app.auth import AuthContext, verify_jwt


@dataclass
class RequestTime:
    count: int
    start_time: float

_user_requests: dict[str, RequestTime] = {}

def check_rate_limit(user_id: str) -> None:
    entry = _user_requests.get(user_id)
    if entry is None or (time.perf_counter() - entry.start_time) > 60:
        _user_requests[user_id] = RequestTime(count=1, start_time=time.perf_counter())
        return
    else:
        entry.count += 1
        if entry.count > 20:
            seconds_remaining = 60 - (time.perf_counter() - entry.start_time)
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded",
                headers={"Retry-After": str(int(seconds_remaining))},
            )

def rate_limit(auth: AuthContext = Depends(verify_jwt)) -> AuthContext: # noqa B008
    check_rate_limit(auth.user_id) 
    return auth
