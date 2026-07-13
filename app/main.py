from fastapi import FastAPI

app = FastAPI(title="smartzen-ai")

@app.get("/health")
def health():
    return {"ok": True}
