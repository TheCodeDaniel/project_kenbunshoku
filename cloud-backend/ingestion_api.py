"""
FastAPI ingestion endpoint. Receives frames from any edge-service instance
(camera-agnostic — doesn't know or care what camera or edge box sent it),
hands them to qwen_client for reasoning, checks memory_store for recurring
patterns, and lets alert_dispatcher decide what to notify.

Deployed on Alibaba Cloud (see deploy/). See CLAUDE.md for the API contract.
"""
from fastapi import BackgroundTasks, FastAPI, UploadFile, Form
from qwen_client import classify_frame
from memory_store import init_db, get_pattern_context, record_visit
from alert_dispatcher import PUSH_ENDPOINT, dispatch_alert, is_suppressed

app = FastAPI(title="Kenbunshoku Ingestion API")


@app.on_event("startup")
async def startup() -> None:
    init_db()


@app.post("/ingest")
async def ingest(
    background_tasks: BackgroundTasks,
    frame: UploadFile,
    camera_id: str = Form(...),
    timestamp: str = Form(...),
):
    """
    Classify the frame and check memory for a recurring pattern, then return
    immediately — the actual push (or suppression) and persisting this visit
    both happen after the response is sent. The edge device only needs the
    classification; it shouldn't have to wait on a second network hop (the
    ntfy.sh push) on top of the Qwen-VL call it's already waiting on.
    """
    frame_bytes = await frame.read()
    result = classify_frame(frame_bytes)
    classification = result["classification"]
    reasoning = result["reasoning"]

    pattern_context = get_pattern_context(camera_id, classification, timestamp)
    alert_sent = bool(PUSH_ENDPOINT) and not is_suppressed(classification, pattern_context)

    background_tasks.add_task(dispatch_alert, camera_id, classification, reasoning, pattern_context)
    background_tasks.add_task(record_visit, camera_id, timestamp, classification, reasoning)

    return {
        "classification": classification,
        "reasoning": reasoning,
        "pattern_context": pattern_context,
        "alert_sent": alert_sent,
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
