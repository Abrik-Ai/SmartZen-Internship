from fastapi import Depends, FastAPI

from app.auth import AuthContext, verify_jwt
from app.status_cache import get_ollama_status

app = FastAPI(title="smartzen-ai")

@app.get("/health") 
def health() -> dict[str, bool]:
    return {"ok": True}

@app.get("/assistant/status")
def assistant_status(_: AuthContext = Depends(verify_jwt)) -> dict[str, bool]: # noqa: B008
    status = get_ollama_status()
    return {"enabled": status}
    
