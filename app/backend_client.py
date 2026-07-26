import httpx

from app.config import BACKEND_API_URL
from app.models.generated import AuthTokens, Schedule


class BackendClient:
    def __init__(self, base_url: str | None = BACKEND_API_URL) -> None:
        if base_url is None:
            raise ValueError("BACKEND_API_URL is not set")
        self.base_url = base_url


    def login(self, email: str, password: str) -> AuthTokens:
        url = self.base_url + "/auth/login"
        response = httpx.post(url, json={"email": email, "password": password})
        data = response.json()
        return AuthTokens.model_validate(data)

    def get_schedules(self, token: str) -> list[Schedule]:
        url = self.base_url + "/schedules/me"
        headers = {"Authorization": f"Bearer {token}"}
        response = httpx.get(url, headers=headers)
        data = response.json()
        return [Schedule.model_validate(item) for item in data]

