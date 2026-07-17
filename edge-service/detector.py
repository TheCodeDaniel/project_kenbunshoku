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
import os
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterator, Optional

import cv2
from ultralytics import YOLO

from forwarder import forward_detection

logger = logging.getLogger(__name__)

PERSON_CLASS_ID = 0  # COCO class index for "person"
DEFAULT_CONFIDENCE_THRESHOLD = 0.5
RECONNECT_DELAY_SECONDS = 2.0
NO_FRAME_TIMEOUT_SECONDS = 5.0  # how long without a fresh frame before we reconnect


@dataclass
class Detection:
    frame_bytes: bytes
    camera_id: str
    timestamp: str
    confidence: float


def load_model(weights: str = "yolov8n.pt") -> YOLO:
    """Load YOLOv8n (open weights, fetched by ultralytics on first use)."""
    return YOLO(weights)


class _LatestFrameReader:
    """
    Continuously reads from `capture` in a background thread and exposes only
    the most recently read frame. A slow consumer (model inference + network
    forwarding, which together can take several seconds per detection) would
    otherwise process an ever-growing backlog of stale buffered frames, since
    cv2.VideoCapture.read() pops from its internal buffer in FIFO order, not
    "what's happening right now." This keeps the buffer permanently drained
    so the consumer always sees a near-real-time frame.
    """

    def __init__(self, capture: cv2.VideoCapture):
        self._capture = capture
        self._lock = threading.Lock()
        self._frame = None
        self._ok = False
        # Seeded to "now" rather than None so a stream that never produces a
        # single frame still ages past NO_FRAME_TIMEOUT_SECONDS and triggers
        # a reconnect, instead of seconds_since_last_frame() reporting 0
        # forever.
        self._last_frame_at: float = time.monotonic()
        self._frames_read = 0
        self._stopped = False
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self) -> None:
        while not self._stopped:
            ok, frame = self._capture.read()
            with self._lock:
                self._ok = ok
                self._frame = frame
                if ok:
                    self._last_frame_at = time.monotonic()
                    self._frames_read += 1
            if not ok:
                time.sleep(0.1)

    def read(self):
        with self._lock:
            return self._ok, self._frame

    def frames_read(self) -> int:
        with self._lock:
            return self._frames_read

    def seconds_since_last_frame(self) -> float:
        with self._lock:
            return time.monotonic() - self._last_frame_at

    def stop(self) -> None:
        self._stopped = True
        self._thread.join(timeout=1.0)


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
    reader = _LatestFrameReader(capture)
    last_processed_frame_count = 0
    try:
        while True:
            if not capture.isOpened() or reader.seconds_since_last_frame() > NO_FRAME_TIMEOUT_SECONDS:
                logger.warning(
                    "stream %s stalled, reconnecting (retry in %.1fs)",
                    stream_url,
                    RECONNECT_DELAY_SECONDS,
                )
                reader.stop()
                capture.release()
                time.sleep(RECONNECT_DELAY_SECONDS)
                capture = cv2.VideoCapture(stream_url)
                reader = _LatestFrameReader(capture)
                last_processed_frame_count = 0
                continue

            ok, frame = reader.read()
            if not ok or frame is None:
                # Reader hasn't produced a first frame yet (or hit a
                # transient read failure it's already retrying internally) —
                # seconds_since_last_frame() above is what decides whether
                # this is actually a dead stream, so just wait briefly.
                time.sleep(0.05)
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

                current_frame_count = reader.frames_read()
                skipped = max(0, current_frame_count - last_processed_frame_count - 1)
                logger.info("skipped %d buffered frame(s) since last detection", skipped)
                last_processed_frame_count = current_frame_count

                yield Detection(
                    frame_bytes=buffer.tobytes(),
                    camera_id=camera_id,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    confidence=best_confidence,
                )
    finally:
        reader.stop()
        capture.release()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    stream_url = os.environ.get("STREAM_URL", "")
    camera_id = os.environ.get("CAMERA_ID", "test-cam-1")
    if not stream_url:
        raise SystemExit("STREAM_URL environment variable is required")

    for detection in watch_stream(stream_url, camera_id):
        result = forward_detection(detection)
        logger.info("forwarded detection (confidence=%.2f): %s", detection.confidence, result)
