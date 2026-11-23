"""Backend API - PLACEHOLDER.  Owners: Sevag (API), Sergei (model in ml/).

The proxy will POST {"url": ...} to /analyze.
TODO: call the ML model instead of returning a fixed answer.
After editing: docker compose restart backend
"""
from fastapi import FastAPI
from ml.predict import predict_url

app = FastAPI(title="MalURL Guard backend")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}

@app.post("/analyze")
def analyze(request: dict) -> dict:
    return predict_url(
        url=request.get("url", ""),
        strictness=request.get("strictness")
    )