import os
import httpx
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class BackendClient:
    
    def __init__(self, token: str):
        self.base_url = os.getenv("BACKEND_API_URL", "http://localhost:4000")
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        self.timeout = 30.0
    
    async def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make a GET request to the backend."""
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers=self.headers,
                    params=params,
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()
                
        except httpx.TimeoutException:
            logger.error(f"Request to {url} timed out")
            raise Exception("Backend request timed out")
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code} from {url}")
            if e.response.status_code == 403:
                raise Exception("Access denied: You don't have permission for this resource")
            if e.response.status_code == 404:
                raise Exception("Resource not found")
            raise Exception(f"Backend error: {e.response.status_code}")
            
        except httpx.RequestError as e:
            logger.error(f"Request error to {url}: {e}")
            raise Exception("Could not connect to backend")