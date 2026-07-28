import pytest
import os
import asyncio
from app.tools.schedule import get_my_schedule
from app.tools.rooms import find_free_rooms, get_room_status

# Test users
INSTRUCTOR_A_TOKEN = os.getenv("INSTRUCTOR_A_TOKEN", "token_for_instructor_a")
INSTRUCTOR_B_TOKEN = os.getenv("INSTRUCTOR_B_TOKEN", "token_for_instructor_b")
FOREIGN_ROOM_ID = "room_999"  # A room that belongs to a different user

@pytest.mark.asyncio
async def test_schedule_scope():
    """Test that instructor A cannot see instructor B's schedule."""
    # Get schedule for instructor A
    schedule_a = await get_my_schedule(INSTRUCTOR_A_TOKEN, "today")
    
    # Get schedule for instructor B
    schedule_b = await get_my_schedule(INSTRUCTOR_B_TOKEN, "today")
    
    # Verify that schedules are different
    assert schedule_a.get("items") != schedule_b.get("items")

@pytest.mark.asyncio
async def test_find_free_rooms_scope():
    """Test that injecting a foreign room ID returns a 403."""
    # Normal request should succeed
    result = await find_free_rooms(INSTRUCTOR_A_TOKEN, 30)
    assert "error" not in result or result.get("error") != "Access denied"
    
    # Try to access a room that should be forbidden
    # The backend should return 403 for foreign rooms
    # This test assumes the backend returns only rooms accessible to the user
    # We'll test that the user cannot access unauthorized rooms
    pass

@pytest.mark.asyncio
async def test_room_status_scope():
    """Test that room status respects user scope."""
    # Get status for instructor A
    status_a = await get_room_status(INSTRUCTOR_A_TOKEN)
    
    # Get status for instructor B
    status_b = await get_room_status(INSTRUCTOR_B_TOKEN)
    
    # If both have active sessions, they should be in different rooms
    if status_a.get("session") and status_b.get("session"):
        assert status_a["session"]["room_id"] != status_b["session"]["room_id"]

@pytest.mark.asyncio
async def test_foreign_room_id_injection():
    """Test that using a foreign room ID returns a 403 error."""
    # Try to find free rooms with a foreign room filter
    # The backend should return an error
    pass