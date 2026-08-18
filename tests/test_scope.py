import os

import httpx
import pytest
import pytest_asyncio

from app.backend_client import BackendClient
from app.tool_errors import ToolForbidden
from app.tools.rooms import find_free_rooms, get_room_status
from app.tools.schedule import get_my_schedule

# Test users
BACKEND_URL = os.getenv("BACKEND_API_URL", "http://localhost:4000")

@pytest_asyncio.fixture(scope="module")
async def token_a() -> str:
    email = os.getenv("INSTRUCTOR_A_EMAIL")
    password = os.getenv("INSTRUCTOR_A_PASSWORD")
    if not email or not password:
        pytest.skip("INSTRUCTOR_A_* not set — live-backend test")
    result = await BackendClient(BACKEND_URL).login(email=email, password=password)
    return result.access_token

@pytest_asyncio.fixture(scope="module")
async def token_b() -> str:
    email = os.getenv("INSTRUCTOR_B_EMAIL")
    password = os.getenv("INSTRUCTOR_B_PASSWORD")
    if not email or not password:
        pytest.skip("INSTRUCTOR_B_* not set — live-backend test")
    result = await BackendClient(BACKEND_URL).login(email=email, password=password)
    return result.access_token

def is_backend_running() -> bool:
    """Check if the backend is reachable."""
    try:
        response = httpx.get(f"{BACKEND_URL}/health", timeout=2.0)
        return response.status_code == 200
    except Exception:
        return False


@pytest.mark.asyncio
async def test_schedule_scope(token_a: str, token_b: str) -> None:
    """Test that instructor A cannot see instructor B's schedule."""
    if not is_backend_running():
        pytest.skip("Backend not running - skipping scope test")
    
    client_a = BackendClient(BACKEND_URL)
    client_b = BackendClient(BACKEND_URL)
    
    schedule_a = await get_my_schedule("today", token_a, client_a)
    schedule_b = await get_my_schedule("today", token_b, client_b)

    # This only proves the two results differ, not that each contains only
    # its own owner's items. ScheduleResponse has no instructor field, so
    # ownership can't be verified from the response alone. Proper isolation
    # testing needs seeded per-instructor schedules or a response reshape.
    if schedule_a or schedule_b:
        assert schedule_a != schedule_b
    else:
        pytest.skip("Neither instructor has a schedule today - nothing to isolate")


@pytest.mark.asyncio
async def test_find_free_rooms_scope(token_a: str, token_b: str) -> None:
    """Test that injecting a foreign room ID returns a 403."""
    if not is_backend_running():
        pytest.skip("Backend not running - skipping scope test")
    
    client_a = BackendClient(BACKEND_URL)
    client_b = BackendClient(BACKEND_URL)
    
    rooms_b = await find_free_rooms(30, token_b, client_b)
    
    if rooms_b:
        foreign_room_id = rooms_b[0].id
        
        try:
            await client_a.get_latest_telemetry(token_a, foreign_room_id)
            raise AssertionError("Should have raised ToolForbidden for foreign room access")
        except ToolForbidden:
            pass


@pytest.mark.asyncio
async def test_room_status_scope(token_a: str, token_b: str) -> None:
    """Test that room status respects user scope."""
    if not is_backend_running():
        pytest.skip("Backend not running - skipping scope test")
    
    client_a = BackendClient(BACKEND_URL)
    client_b = BackendClient(BACKEND_URL)
    
    status_a = await get_room_status(token_a, client_a)
    status_b = await get_room_status(token_b, client_b)
    
    if status_a.session and status_b.session:
        assert status_a.session["room_id"] != status_b.session["room_id"]


@pytest.mark.asyncio
async def test_foreign_room_id_injection(token_a: str, token_b: str) -> None:
    """Test that using a foreign room ID returns a 403 error."""
    if not is_backend_running():
        pytest.skip("Backend not running - skipping scope test")
    
    client_a = BackendClient(BACKEND_URL)
    client_b = BackendClient(BACKEND_URL)
    
    rooms_b = await find_free_rooms(30, token_b, client_b)
    
    if rooms_b:
        foreign_room_id = rooms_b[0].id
        
        try:
            await client_a.get_latest_telemetry(token_a, foreign_room_id)
            raise AssertionError("Should have raised ToolForbidden for foreign room access")
        except ToolForbidden:
            pass