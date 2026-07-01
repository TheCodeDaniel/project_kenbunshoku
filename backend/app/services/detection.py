"""YOLO object detection service."""

import base64
import io
import json
import logging
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from ultralytics import YOLO

logger = logging.getLogger(__name__)


class DetectionService:
    """Handles YOLO-based object detection for security monitoring."""

    def __init__(self, config_path: str = "../config.json"):
        self.config = self._load_config(config_path)
        self.model: Optional[YOLO] = None
        self.familiar_faces: dict[str, list[str]] = {}
        self.alert_cooldowns: dict[str, float] = {}  # person_id -> last_alert_time

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from JSON file."""
        full_path = Path(__file__).parent.parent.parent / config_path
        try:
            with open(full_path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Config file not found at {full_path}, using defaults")
            return {
                "yolo": {"model_path": "../models/yolov8n.pt", "conf_threshold": 0.25, "iou_threshold": 0.45},
                "detection": {"target_classes": ["person", "vehicle"], "alert_cooldown_seconds": 30}
            }

    def load_model(self) -> None:
        """Load YOLO model from configured path."""
        model_path = Path(__file__).parent.parent.parent / self.config["yolo"]["model_path"]

        if not model_path.exists():
            logger.warning(f"YOLO model not found at {model_path}, downloading yolov8n.pt")
            # Download and save the default model
            model = YOLO("yolov8n.pt")
            model.save(model_path)
            self.model = model
        else:
            logger.info(f"Loading YOLO model from {model_path}")
            self.model = YOLO(str(model_path))

    def load_familiar_faces(self, store_path: Optional[str] = None) -> None:
        """Load previously registered familiar faces."""
        if store_path is None:
            store_path = self.config["detection"].get("familiar_faces_store", "familiar_faces.json")

        full_path = Path(__file__).parent.parent / store_path
        try:
            with open(full_path, "r") as f:
                self.familiar_faces = json.load(f)
            logger.info(f"Loaded {len(self.familiar_faces)} familiar faces")
        except FileNotFoundError:
            self.familiar_faces = {}
            logger.info("No existing familiar faces file found")

    def save_familiar_faces(self, store_path: Optional[str] = None) -> None:
        """Save registered familiar faces to disk."""
        if store_path is None:
            store_path = self.config["detection"].get("familiar_faces_store", "familiar_faces.json")

        full_path = Path(__file__).parent.parent / store_path
        with open(full_path, "w") as f:
            json.dump(self.familiar_faces, f, indent=2)
        logger.info(f"Saved {len(self.familiar_faces)} familiar faces to {full_path}")

    def decode_frame(self, base64_data: str) -> np.ndarray:
        """Decode a Base64 encoded image frame."""
        # Remove data URL prefix if present
        if "," in base64_data:
            base64_data = base64_data.split(",")[1]

        img_data = base64.b64decode(base64_data)
        np_array = np.frombuffer(img_data, dtype=np.uint8)
        return cv2.imdecode(np_array, cv2.IMREAD_COLOR)

    def detect_objects(self, frame: np.ndarray) -> list[dict]:
        """Run YOLO detection on a single frame.

        Args:
            frame: OpenCV image (BGR format).

        Returns:
            List of detected objects with class names and bounding boxes.
        """
        if self.model is None:
            raise RuntimeError("YOLO model not loaded. Call load_model() first.")

        # Run detection
        results = self.model(frame, conf=self.config["yolo"]["conf_threshold"], iou=self.config["yolo"]["iou_threshold"])

        detections = []
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    class_id = int(box.cls[0])
                    confidence = float(box.conf[0])
                    x1, y1, x2, y2 = map(int, box.xyxy[0])

                    # Get class name from the model
                    class_name = self.model.names[class_id]

                    detections.append({
                        "class_name": class_name,
                        "confidence": confidence,
                        "x_min": max(0, x1),
                        "y_min": max(0, y1),
                        "x_max": min(frame.shape[1], x2),
                        "y_max": min(frame.shape[0], y2)
                    })

        logger.debug(f"Detected {len(detections)} objects")
        return detections

    def detect_on_frame(self, base64_data: str) -> list[dict]:
        """Convenience method to decode and detect on a Base64 frame."""
        frame = self.decode_frame(base64_data)
        return self.detect_objects(frame)

    def is_familiar_face(self, description: str) -> tuple[bool, Optional[str]]:
        """Check if the person's description matches any familiar face.

        Args:
            description: Text description of the person (from Qwen or YOLO).

        Returns:
            Tuple of (is_familiar, name).
        """
        desc_lower = description.lower()
        for name, descriptions in self.familiar_faces.items():
            for desc in descriptions:
                if desc in desc_lower or desc_lower in desc:
                    return True, name
        return False, None

    def check_alert_cooldown(self, person_id: str) -> bool:
        """Check if alert cooldown has passed for a person.

        Returns True if we CAN send an alert (cooldown expired or no prior alert).
        """
        cooldown = self.config["detection"].get("alert_cooldown_seconds", 30)
        import time
        current_time = time.time()

        if person_id not in self.alert_cooldowns:
            return True

        elapsed = current_time - self.alert_cooldowns[person_id]
        if elapsed >= cooldown:
            # Cooldown expired, allow new alert
            self.alert_cooldowns[person_id] = current_time
            return True

        return False

    def register_familiar_face(self, name: str, description: str) -> None:
        """Register a person as familiar/safe."""
        if name not in self.familiar_faces:
            self.familiar_faces[name] = []
        if description not in self.familiar_faces[name]:
            self.familiar_faces[name].append(description)
        self.save_familiar_faces()

    def get_target_detections(self, detections: list[dict]) -> list[dict]:
        """Filter detections to only target classes."""
        target_classes = set(self.config["detection"].get("target_classes", ["person", "vehicle"]))
        return [d for d in detections if d["class_name"] in target_classes]