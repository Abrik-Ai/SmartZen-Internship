import logging
from typing import Optional, Dict, Any
from app.tools.client import BackendClient

logger = logging.getLogger(__name__)

async def find_free_rooms(
    token: str,
    minutes_needed: int,
    start_time: Optional[str] = None
) -> Dict[str, Any]:
    """
    Find free rooms for a given time window.
    
    Args:
        token: The user's authentication token
        minutes_needed: How many minutes the room is needed for
        start_time: Optional start time (ISO format). If not provided, uses current time.
    
    Returns:
        Dict containing list of free rooms with their next class
    """
    client = BackendClient(token)
    
    endpoint = "/rooms/empty"
    params = {"minutes": minutes_needed}
    
    if start_time:
        params["start"] = start_time
    
    logger.info(f"Finding free rooms for {minutes_needed} minutes")
    logger.info(f"Params: {params}")
    
    try:
        result = await client.get(endpoint, params)
        logger.info(f"Found {len(result.get('rooms', []))} free rooms")
        return result
    except Exception as e:
        logger.error(f"Failed to find free rooms: {e}")
        return {"rooms": [], "error": str(e)}


async def get_room_status(token: str) -> Dict[str, Any]:
    """
    Get the user's active session and room status.
    
    Args:
        token: The user's authentication token
    
    Returns:
        Dict containing active session and telemetry data
    """
    client = BackendClient(token)
    
    # Step 1: Get active sessions
    try:
        sessions = await client.get("/api/active-sessions")
        if not sessions.get("sessions"):
            return {"session": None, "telemetry": None, "message": "No active session"}
        
        # Take the first active session
        active_session = sessions["sessions"][0]
        room_id = active_session.get("room_id")
        
        if not room_id:
            return {"session": active_session, "telemetry": None}
        
        # Step 2: Get latest telemetry for the room
        telemetry = await client.get(f"/rooms/{room_id}/latest-telemetry")
        
        return {
            "session": active_session,
            "telemetry": telemetry
        }
        
    except Exception as e:
        logger.error(f"Failed to get room status: {e}")
        return {
            "session": None,
            "telemetry": None,
            "error": str(e)
        }