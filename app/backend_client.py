import httpx

from app.config import BACKEND_API_URL
from app.models.generated import AuthTokens, Schedule, EmptyRoom
from app.tools_call import call_with_retries
from typing import cast, Any


class BackendClient:
    def __init__(self, base_url: str | None = BACKEND_API_URL) -> None:
        if base_url is None: # in case the environment variable is not set
            raise ValueError("BACKEND_API_URL is not set")
        self.base_url = base_url


    async def login(self, email: str, password: str) -> AuthTokens:
        url = self.base_url + "/auth/login"
        async with httpx.AsyncClient() as client:
            response = await call_with_retries(
                lambda: client.post(url, json={"email": email, "password": password}, timeout=10)
                )
        data = response.json() # to convert JSON to a Python dictionary
        return AuthTokens.model_validate(data)

    async def get_schedules(self, token: str, 
                      from_time: str | None = None, to_time: str | None = None
                      ) -> list[Schedule]:
        url = self.base_url + "/schedules/me"
        headers = {"Authorization": f"Bearer {token}"}
        #headers = {"Authorization": f"Bearer fake-token"} - to test the faked token
        params = {}
        if from_time is not None:
            params["from"] = from_time
        if to_time is not None:
            params["to"] = to_time
        async with httpx.AsyncClient() as client:    
            response = await call_with_retries(
                lambda: client.get(url, headers=headers, params=params, timeout=10)
                )
        data = response.json()  
        return [Schedule.model_validate(item) for item in data]

  # ===== ROOM TOOLS =====

    async def get_empty_rooms(
        self,
        token: str,
        minutes: int,
        start: str | None = None
    ) -> list[EmptyRoom]:
        """Fetch empty rooms from /rooms/empty."""
        url = self.base_url + "/rooms/empty"
        headers = {"Authorization": f"Bearer {token}"}
        params: dict[str, int | str] = {"minutes": minutes}
        if start is not None:
            params["start"] = start

        async with httpx.AsyncClient() as client:
            response = await call_with_retries(
                lambda: client.get(url, headers=headers, params=params, timeout=10)
            )
        data = response.json()
        return [EmptyRoom.model_validate(item) for item in data.get("rooms", [])]

    async def get_active_sessions(self, token: str) -> dict[str, Any]:
        """Fetch active sessions from /sessions/active."""
        url = self.base_url + "/sessions/active"
        headers = {"Authorization": f"Bearer {token}"}

        async with httpx.AsyncClient() as client:
            response = await call_with_retries(
                lambda: client.get(url, headers=headers, timeout=10)
            )
        return cast(dict[str, Any], response.json())

    async def get_latest_telemetry(self, token: str, room_id: str) -> dict[str, Any]:
        """Fetch latest telemetry from /telemetry/{room_id}/latest."""
        url = self.base_url + f"/telemetry/{room_id}/latest"
        headers = {"Authorization": f"Bearer {token}"}

        async with httpx.AsyncClient() as client:
            response = await call_with_retries(
                lambda: client.get(url, headers=headers, timeout=10)
            )
        return cast(dict[str, Any], response.json())