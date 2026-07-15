"""
Local person/motion detection.

Pulls frames from a camera stream (real IP camera in production, phone-based
test stream during MVP development — see camera-simulator/README.md) and runs
YOLOv8n to flag person-present frames. Positive detections are handed to
forwarder.py, which crops and sends them to the cloud ingestion API.

Camera-agnostic: this module should never assume a specific device. The stream
URL is configuration, not a hardcoded value.
"""
from dataclasses import dataclass


@dataclass
class Detection:
    frame_bytes: bytes
    camera_id: str
    timestamp: str
    confidence: float


def load_model():
    """Load YOLOv8n (open weights). TODO: pull from ultralytics."""
    raise NotImplementedError


def watch_stream(stream_url: str, camera_id: str):
    """
    Continuously read frames from `stream_url`, run detection, and yield
    Detection objects for frames containing a person above the confidence
    threshold. TODO: implement with opencv-python / ultralytics.
    """
    raise NotImplementedError
