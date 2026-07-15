"""
FastAPI ingestion endpoint. Receives frames from any edge-service instance
(camera-agnostic — doesn't know or care what camera or edge box sent it),
hands them to qwen_client for reasoning, checks memory_store for recurring
patterns, and lets alert_dispatcher decide what to notify.

Deployed on Alibaba Cloud (see deploy/). See CLAUDE.md for the API contract.
"""
from fastapi import FastAPI, UploadFile, Form
from qwen_client import classify_frame
from memory_store import get_pattern_context, record_visit
from alert_dispatcher import dispatch_alert

app = FastAPI(title="Kenbunshoku Ingestion API")


@app.post("/ingest")
async def ingest(frame: UploadFile, camera_id: str = Form(...), timestamp: str = Form(...)):
    """
    TODO:
    1. Read frame bytes
    2. classify_frame(frame_bytes) -> Qwen-VL classification + reasoning
    3. get_pattern_context(camera_id, classification) -> recurring-visit context
    4. dispatch_alert(...) -> decide + send push notification
    5. record_visit(...) -> persist this visit for future pattern matching
    6. Return { classification, reasoning, alert_sent }
    """
    raise NotImplementedError


@app.get("/health")
async def health():
    return {"status": "ok"}
