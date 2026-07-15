"""
Forwards positive detections to the cloud ingestion API.

Sends only cropped, motion-triggered frames — never continuous raw video —
to stay bandwidth-aware, per the EdgeAgent track's requirements.
"""
import logging
import os
import time
from typing import Optional

import requests

logger = logging.getLogger(__name__)

CLOUD_INGEST_URL = os.environ.get("CLOUD_INGEST_URL", "http://localhost:8000/ingest")
MAX_ATTEMPTS = 3
INITIAL_BACKOFF_SECONDS = 1.0
REQUEST_TIMEOUT_SECONDS = 10.0


def forward_detection(detection) -> dict:
    """
    POST a Detection (see detector.py) to the cloud ingestion API.
    Returns the parsed JSON response: classification, reasoning, alert_sent.

    Retries with exponential backoff on connection failure. If the cloud is
    still unreachable after all attempts, falls back to a local, informational
    alert rather than raising — the system must still notify the homeowner
    even when Qwen-VL reasoning is unavailable (never silence, never a
    control action; see CLAUDE.md's "no autonomous actions" constraint).
    """
    files = {"frame": ("frame.jpg", detection.frame_bytes, "image/jpeg")}
    data = {"camera_id": detection.camera_id, "timestamp": detection.timestamp}

    backoff = INITIAL_BACKOFF_SECONDS
    last_error: Optional[Exception] = None

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = requests.post(
                CLOUD_INGEST_URL, files=files, data=data, timeout=REQUEST_TIMEOUT_SECONDS
            )
            response.raise_for_status()
            return response.json()
        except (requests.ConnectionError, requests.Timeout, requests.HTTPError) as exc:
            last_error = exc
            logger.warning("ingest POST failed (attempt %d/%d): %s", attempt, MAX_ATTEMPTS, exc)
            if attempt < MAX_ATTEMPTS:
                time.sleep(backoff)
                backoff *= 2

    logger.error(
        "cloud unreachable after %d attempts, falling back to local alert: %s",
        MAX_ATTEMPTS,
        last_error,
    )
    return _local_fallback_alert(detection, last_error)


def _local_fallback_alert(detection, error: Optional[Exception]) -> dict:
    """
    Cloud-unreachable fallback: an informational, local-only notice that a
    person was detected but couldn't be classified by Qwen-VL. Mirrors the
    /ingest response shape so callers don't need to special-case it. Never
    triggers a control action — only ever a notification.
    """
    logger.warning(
        "LOCAL ALERT: person detected on camera '%s' at %s (cloud unreachable: %s)",
        detection.camera_id,
        detection.timestamp,
        error,
    )
    return {
        "classification": "anomalous",
        "reasoning": "Cloud backend unreachable; local fallback alert issued without Qwen-VL reasoning.",
        "alert_sent": True,
    }
