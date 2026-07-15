"""
FastAPI ingestion endpoint. Receives frames from any edge-service instance
(camera-agnostic — doesn't know or care what camera or edge box sent it),
hands them to qwen_client for reasoning, checks memory_store for recurring
patterns, and lets alert_dispatcher decide what to notify.

Deployed on Alibaba Cloud (see deploy/). See CLAUDE.md for the API contract.
"""
from fastapi import FastAPI, UploadFile, Form
from qwen_client import classify_frame

app = FastAPI(title="Kenbunshoku Ingestion API")


@app.post("/ingest")
async def ingest(frame: UploadFile, camera_id: str = Form(...), timestamp: str = Form(...)):
    """
    Detection in, classification out. Memory/pattern context and alert
    dispatch land once memory_store and alert_dispatcher are implemented
    (build order steps 3-4 in CLAUDE.md); for now alert_sent is always False.
    """
    frame_bytes = await frame.read()
    result = classify_frame(frame_bytes)
    return {
        "classification": result["classification"],
        "reasoning": result["reasoning"],
        "alert_sent": False,
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
