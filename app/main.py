from fastapi import FastAPI

app = FastAPI(title="smartzen-ai")

@app.get("/health") 
def health() -> dict[str, bool]:
    return {"ok": True}
