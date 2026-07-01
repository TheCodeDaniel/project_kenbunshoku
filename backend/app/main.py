"""FastAPI application for Project Kenbunshoku - Predictive Security System."""

import asyncio
import base64
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.models import AlertRequest, AlertResponse, HealthResponse, RegisterFaceRequest
from app.services.detection import DetectionService
from app.services.qwen_agent import QwenAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize services
detection_service = DetectionService()
qwen_agent = QwenAgent()


# ─── FastAPI App ──────────────────────────────────────────────────────────────

app = FastAPI(
    title="Kenbunshoku Security System",
    description="Predictive security system using YOLO detection and Qwen-VL semantic analysis",
    version="1.0.0"
)

# CORS middleware for mobile app communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# ─── Lifecycle ────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup_event():
    """Load models and familiar faces on startup."""
    logger.info("Kenbunshoku backend starting up...")
    try:
        detection_service.load_model()
        logger.info("YOLO model loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load YOLO model: {e}")

    try:
        detection_service.load_familiar_faces()
        logger.info("Familiar faces database loaded.")
    except Exception as e:
        logger.warning(f"Could not load familiar faces: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Save state on shutdown."""
    try:
        detection_service.save_familiar_faces()
        logger.info("Familiar faces saved before shutdown.")
    except Exception as e:
        logger.error(f"Failed to save familiar faces: {e}")


# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/", tags=["Root"])
async def root():
    """Health check and API info."""
    return {
        "name": "Kenbunshoku Security System",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health", response_model=HealthResponse, tags=["Monitoring"])
async def health_check():
    """Detailed health check."""
    return HealthResponse(
        status="ok",
        yolo_loaded=detection_service.model is not None,
        qwen_configured=bool(qwen_agent.api_key and qwen_agent.api_key != "your-dashscope-api-key-here"),
        familiar_faces_count=len(detection_service.familiar_faces),
        uptime_seconds=time.time()
    )


@app.post(
    "/analyze_frame",
    response_model=AlertResponse,
    tags=["Detection"]
)
async def analyze_frame(request: AlertRequest):
    """Analyze a single video frame for security threats.

    This is the primary endpoint used by the mobile app. It receives a Base64
    encoded image frame, runs YOLO detection, and if persons are detected,
    sends them to Qwen-VL for semantic threat assessment.

    Args:
        request: AlertRequest with base64 frame data and metadata.

    Returns:
        AlertResponse with status (safe/threat/unknown), confidence, message.
    """
    try:
        # Step 1: Decode the Base64 frame
        detections = detection_service.detect_on_frame(request.frame)

        if not detections:
            return AlertResponse(
                status="clear",
                confidence=0.0,
                message="No objects detected in frame.",
                timestamp=datetime.utcnow().isoformat()
            )

        # Step 2: Filter for target classes (persons, vehicles)
        target_detections = detection_service.get_target_detections(detections)

        if not target_detections:
            return AlertResponse(
                status="clear",
                confidence=0.0,
                message=f"Detected {len(detections)} objects but none are security-relevant.",
                timestamp=datetime.utcnow().isoformat()
            )

        # Step 3: For each person detection, run Qwen analysis
        primary_result = None
        all_results = []

        for det in target_detections:
            if det["class_name"] == "person":
                qwen_analysis = qwen_agent.analyze_threat(
                    frame=detection_service.decode_frame(request.frame),
                    bbox=det,
                    person_description=""
                )

                enriched_result = dict(det)
                if qwen_analysis:
                    enriched_result.update(qwen_analysis)

                all_results.append(enriched_result)

                # Track the highest-confidence threat
                if primary_result is None or (
                    qwen_analysis and qwen_analysis.get("confidence", 0) > primary_result.get("confidence", 0)
                ):
                    primary_result = enriched_result

            elif det["class_name"] == "vehicle":
                all_results.append({**det, "threat_level": "safe"})

        if not all_results:
            return AlertResponse(
                status="clear",
                confidence=0.0,
                message="No persons detected.",
                timestamp=datetime.utcnow().isoformat()
            )

        # Step 4: Determine overall alert status from best analysis
        if primary_result is None:
            primary_result = all_results[0]

        threat_level = primary_result.get("threat_level", "unknown")
        familiar_name = None

        # Check if this person is a registered familiar face
        desc = primary_result.get("description", "")
        is_familiar, name = detection_service.is_familiar_face(desc)

        if is_familiar:
            threat_level = "safe"
            familiar_name = name

        # Step 5: Determine final status
        if threat_level == "threat":
            status = "threat"
            message = f"Potential security threat detected! {desc[:200]}"
        elif threat_level == "safe" or is_familiar:
            status = "safe"
            if familiar_name:
                message = f"Familiar face identified: {familiar_name}"
            else:
                message = "Person detected, assessed as safe."
        else:
            status = "unknown"
            message = f"Detection requires review. Objects: {[d['class_name'] for d in all_results]}"

        # Step 6: Enrich response with detection details
        return AlertResponse(
            status=status,
            confidence=primary_result.get("confidence", 0.5),
            message=message,
            detections=all_results,
            timestamp=datetime.utcnow().isoformat(),
            familiar_name=familiar_name
        )

    except Exception as e:
        logger.error(f"Error analyzing frame: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal analysis error: {str(e)}")


@app.post(
    "/register_face",
    tags=["Management"]
)
async def register_familiar_face(request: RegisterFaceRequest):
    """Register a person as familiar/safe.

    This helps the system learn and stop sending alerts for known people
    like delivery drivers, neighbors, or police officers.

    Args:
        request: Name and description of the familiar person.

    Returns:
        Success message confirming registration.
    """
    detection_service.register_familiar_face(request.name, request.description)

    return {
        "status": "success",
        "message": f"Registered '{request.name}' as a familiar face.",
        "total_registered": len(detection_service.familiar_faces)
    }


@app.get(
    "/familiar_faces",
    tags=["Management"]
)
async def list_familiar_faces():
    """List all registered familiar faces."""
    return {
        "faces": [
            {"name": name, "descriptions": descs}
            for name, descs in detection_service.familiar_faces.items()
        ]
    }


@app.delete(
    "/familiar_faces/{name}",
    tags=["Management"]
)
async def remove_familiar_face(name: str):
    """Remove a familiar face registration."""
    if name in detection_service.familiar_faces:
        del detection_service.familiar_faces[name]
        detection_service.save_familiar_faces()
        return {"status": "success", "message": f"Removed '{name}' from familiar faces."}

    raise HTTPException(status_code=404, detail=f"'{name}' not found in familiar faces.")


@app.post(
    "/stream/start",
    tags=["Streaming"]
)
async def start_stream():
    """Start a continuous monitoring stream."""
    logger.info("Stream session started")
    return {
        "status": "started",
        "session_id": str(int(time.time())),
        "message": "Ready to receive frames. Use /analyze_frame endpoint."
    }


@app.post(
    "/stream/stop",
    tags=["Streaming"]
)
async def stop_stream(session_id: Optional[str] = None):
    """Stop a monitoring stream session."""
    logger.info(f"Stream session stopped: {session_id or 'unknown'}")
    return {"status": "stopped", "session_id": session_id}


# ─── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )