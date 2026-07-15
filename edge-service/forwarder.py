"""
Forwards positive detections to the cloud ingestion API.

Sends only cropped, motion-triggered frames — never continuous raw video —
to stay bandwidth-aware, per the EdgeAgent track's requirements.
"""
import os
import requests

CLOUD_INGEST_URL = os.environ.get("CLOUD_INGEST_URL", "http://localhost:8000/ingest")


def forward_detection(detection) -> dict:
    """
    POST a Detection (see detector.py) to the cloud ingestion API.
    Returns the parsed JSON response: classification, reasoning, alert_sent.
    TODO: add retry/backoff for flaky connections; this is also where the
    "graceful degradation if cloud unreachable" fallback should trigger a
    local generic alert instead of raising.
    """
    raise NotImplementedError
