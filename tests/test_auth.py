import os
import time

import jwt
from fastapi import Depends, FastAPI, Request
from fastapi.testclient import TestClient

from app.auth import verify_jwt

app = FastAPI()
client = TestClient(app)

@app.get("/protected")
def protected_route(request: Request, auth: None = Depends(verify_jwt)) -> dict[str, str | None]:  # noqa: B008 
    #call the verify_jwt function to check the token
    return {
        "user_id": request.state.auth.user_id, 
        "role": request.state.auth.role,
        "building": request.state.auth.building,
        "faculty": request.state.auth.faculty,
    }

def test_expired_token() -> None:
    expired_payload = {
        "sub": "user123",
        "role": "SUPER_ADMIN",
        "exp": int(time.time()) - 10  # Expired 10 seconds ago
    }

    token = jwt.encode(expired_payload, os.getenv("JWT_ACCESS_SECRET"), algorithm="HS256")
    response = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Token has expired"

def test_invalid_signature() -> None:
    valid_payload = {
        "sub": "user321",
        "role": "INSTRUCTOR",
        "exp": int(time.time()) + 100 # Valid for 100 seconds
    }

    token = jwt.encode(valid_payload, "wrong_secret", algorithm="HS256") # Using a wrong secret key
    response = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token"

def test_missing_header() -> None:
    response = client.get("/protected")
    assert response.status_code == 401
    assert response.json()["detail"] == "Missing or invalid Authorization header"   

def test_wrong_format() -> None:
    response = client.get("/protected", headers={"Authorization": "InvalidFormat"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Missing or invalid Authorization header"

def test_valid_token() -> None:
    valid_payload = {
        "sub": "user555",
        "role": "FACULTY_COORDINATOR",
        "building": "ST Building",
        "faculty": "Engineering",
        "exp": int(time.time()) + 100
    }

    token = jwt.encode(valid_payload, os.getenv("JWT_ACCESS_SECRET"), algorithm="HS256")
    response = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    data = response.json()
    assert response.status_code == 200
    assert data["user_id"] == "user555"
    assert data["role"] == "FACULTY_COORDINATOR"
    assert data["building"] == "ST Building"
    assert data["faculty"] == "Engineering"