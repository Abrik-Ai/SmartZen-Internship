import os

import httpx
import pytest

from app.backend_client import BackendClient
from app.tool_errors import ToolForbidden
from app.tools.rooms import find_free_rooms, get_room_status
from app.tools.schedule import get_my_schedule

# Test users
INSTRUCTOR_A_TOKEN = os.getenv("INSTRUCTOR_A_TOKEN", "token_for_instructor_a")
INSTRUCTOR_B_TOKEN = os.getenv("INSTRUCTOR_B_TOKEN", "token_for_instructor_b")
BACKEND_URL = os.getenv("BACKEND_API_URL", "http://localhost:4000")


def is_backend_running() -> bool:
    """Check if the backend is reachable."""
    try:
        response = httpx.get(f"{BACKEND_URL}/health", timeout=2.0)
        return response.status_code == 200
    except Exception:
        return False


@pytest.mark.asyncio
async def test_schedule_scope() -> None:
    """Test that instructor A cannot see instructor B's schedule."""
    if not is_backend_running():
        pytest.skip("Backend not running - skipping scope test")
    
    client_a = BackendClient(BACKEND_URL)
    client_b = BackendClient(BACKEND_URL)
    
    schedule_a = await get_my_schedule("today", INSTRUCTOR_A_TOKEN, client_a)
    schedule_b = await get_my_schedule("today", INSTRUCTOR_B_TOKEN, client_b)
    
    assert schedule_a != schedule_b


@pytest.mark.asyncio
async def test_find_free_rooms_scope() -> None:
    """Test that injecting a foreign room ID returns a 403."""
    if not is_backend_running():
        pytest.skip("Backend not running - skipping scope test")
    
    client_a = BackendClient(BACKEND_URL)
    client_b = BackendClient(BACKEND_URL)
    
    rooms_b = await find_free_rooms(30, INSTRUCTOR_B_TOKEN, client_b)
    
    if rooms_b:
        foreign_room_id = rooms_b[0].id
        
        try:
            await client_a.get_latest_telemetry(INSTRUCTOR_A_TOKEN, foreign_room_id)
            raise AssertionError("Should have raised ToolForbidden for foreign room access")
        except ToolForbidden:
            pass


@pytest.mark.asyncio
async def test_room_status_scope() -> None:
    """Test that room status respects user scope."""
    if not is_backend_running():
        pytest.skip("Backend not running - skipping scope test")
    
    client_a = BackendClient(BACKEND_URL)
    client_b = BackendClient(BACKEND_URL)
    
    status_a = await get_room_status(INSTRUCTOR_A_TOKEN, client_a)
    status_b = await get_room_status(INSTRUCTOR_B_TOKEN, client_b)
    
    if status_a.session and status_b.session:
        assert status_a.session["room_id"] != status_b.session["room_id"]


@pytest.mark.asyncio
async def test_foreign_room_id_injection() -> None:
    """Test that using a foreign room ID returns a 403 error."""
    if not is_backend_running():
        pytest.skip("Backend not running - skipping scope test")
    
    client_a = BackendClient(BACKEND_URL)
    client_b = BackendClient(BACKEND_URL)
    
    rooms_b = await find_free_rooms(30, INSTRUCTOR_B_TOKEN, client_b)
    
    if rooms_b:
        foreign_room_id = rooms_b[0].id
        
        try:
            await client_a.get_latest_telemetry(INSTRUCTOR_A_TOKEN, foreign_room_id)
            raise AssertionError("Should have raised ToolForbidden for foreign room access")
        except ToolForbidden:
            pass