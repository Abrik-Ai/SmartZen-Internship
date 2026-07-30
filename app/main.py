from fastapi import Depends, FastAPI

from app.auth import AuthContext
from app.ollama_rate_limit import rate_limit
from app.status_cache import get_ollama_status

app = FastAPI(title="smartzen-ai")

@app.get("/health") 
def health() -> dict[str, bool]:
    return {"ok": True}

@app.get("/assistant/status")
def assistant_status(_: AuthContext = Depends(rate_limit)) -> dict[str, bool]: # noqa: B008
    status = get_ollama_status()
    return {"enabled": status}
    
