import logging
from typing import Optional, Dict, Any
from app.tools.client import BackendClient

logger = logging.getLogger(__name__)

async def get_my_schedule(token: str, range: str = "today") -> Dict[str, Any]:
    """
    Get the user's schedule for a specified time range.
    
    Args:
        token: The user's authentication token
        range: One of "today", "this_week", "upcoming"
    
    Returns:
        Dict containing the user's schedule
    """
    client = BackendClient(token)
    
    # Map the range parameter to the backend's expected format
    range_map = {
        "today": "today",
        "this week": "this_week",
        "upcoming": "upcoming"
    }
    
    backend_range = range_map.get(range.lower(), "today")
    
    endpoint = f"/api/schedule"
    params = {"range": backend_range}
    
    logger.info(f"Fetching schedule for range: {backend_range}")
    
    try:
        result = await client.get(endpoint, params)
        logger.info(f"Schedule fetched successfully with {len(result.get('items', []))} items")
        return result
    except Exception as e:
        logger.error(f"Failed to fetch schedule: {e}")
        # Return empty schedule on error
        return {
            "items": [],
            "range": backend_range,
            "error": str(e)
        }