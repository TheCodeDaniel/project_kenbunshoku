"""
Local person/motion detection.

Pulls frames from a camera stream (real IP camera in production, phone-based
test stream during MVP development — see camera-simulator/README.md) and runs
YOLOv8n to flag person-present frames. Positive detections are handed to
forwarder.py, which crops and sends them to the cloud ingestion API.

Camera-agnostic: this module should never assume a specific device. The stream
URL is configuration, not a hardcoded value.
"""
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterator, Optional

import cv2
from ultralytics import YOLO

logger = logging.getLogger(__name__)

PERSON_CLASS_ID = 0  # COCO class index for "person"
DEFAULT_CONFIDENCE_THRESHOLD = 0.5
RECONNECT_DELAY_SECONDS = 2.0


@dataclass
class Detection:
    frame_bytes: bytes
    camera_id: str
    timestamp: str
    confidence: float


def load_model(weights: str = "yolov8n.pt") -> YOLO:
    """Load YOLOv8n (open weights, fetched by ultralytics on first use)."""
    return YOLO(weights)


def watch_stream(
    stream_url: str,
    camera_id: str,
    model: Optional[YOLO] = None,
    confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
) -> Iterator[Detection]:
    """
    Continuously read frames from `stream_url`, run detection, and yield
    Detection objects for frames containing a person above the confidence
    threshold.

    `stream_url` is opaque config (RTSP/HTTP-MJPEG/device index) — this
    function makes no assumption about the camera behind it. Drops in the
    stream trigger a reconnect rather than raising, since flaky test hardware
    (phones) and real cameras alike can blip.
    """
    if model is None:
        model = load_model()

    capture = cv2.VideoCapture(stream_url)
    try:
        while True:
            if not capture.isOpened():
                logger.warning(
                    "stream %s not open, retrying in %.1fs", stream_url, RECONNECT_DELAY_SECONDS
                )
                time.sleep(RECONNECT_DELAY_SECONDS)
                capture.open(stream_url)
                continue

            ok, frame = capture.read()
            if not ok:
                logger.warning("failed to read frame from %s, reconnecting", stream_url)
                capture.release()
                time.sleep(RECONNECT_DELAY_SECONDS)
                capture = cv2.VideoCapture(stream_url)
                continue

            results = model.predict(frame, verbose=False)
            best_confidence = 0.0
            for result in results:
                for box in result.boxes:
                    if int(box.cls[0]) != PERSON_CLASS_ID:
                        continue
                    best_confidence = max(best_confidence, float(box.conf[0]))

            if best_confidence >= confidence_threshold:
                ok, buffer = cv2.imencode(".jpg", frame)
                if not ok:
                    logger.warning("failed to encode frame from %s", stream_url)
                    continue
                yield Detection(
                    frame_bytes=buffer.tobytes(),
                    camera_id=camera_id,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    confidence=best_confidence,
                )
    finally:
        capture.release()
