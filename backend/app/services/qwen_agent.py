"""Qwen Cloud agentic layer for semantic analysis."""

import base64
import io
import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class QwenAgent:
    """Handles semantic analysis using Alibaba Cloud Qwen-VL API."""

    # Default prompt template for threat assessment
    THREAT_ASSESSMENT_PROMPT = """Analyze this image frame from a security camera. Focus on the detected person (cropped region).

Describe:
1. Physical appearance and clothing
2. Any objects being carried or held
3. Body posture and movement intent
4. Threat level assessment (low/medium/high)
5. Is this person potentially dangerous?

Provide a concise analysis for security monitoring purposes."""

    FAMILIAR_FACE_PROMPT = """Analyze the person in this image. Describe their appearance, clothing, accessories, and any distinguishing features that could help identify them as a known person (delivery driver, neighbor, police officer, etc.)."""

    def __init__(self, config_path: str = "../config.json"):
        self.config = self._load_config(config_path)
        self.api_key = self.config.get("qwen", {}).get("api_key", "")
        self.model = self.config.get("qwen", {}).get("model", "qwen-vl-max")
        # Base URL for Dashscope Qwen-VL API
        self.base_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from JSON file."""
        full_path = Path(__file__).parent.parent.parent / config_path
        try:
            with open(full_path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Config file not found at {full_path}, using defaults")
            return {"qwen": {"api_key": "", "model": "qwen-vl-max"}}

    def _encode_image_for_qwen(self, frame: bytes, bbox: dict) -> tuple[bytes, dict]:
        """Encode a cropped image from the frame for Qwen-VL API.

        Returns:
            Tuple of (base64_data, mime_type).
        """
        x_min = int(bbox.get("x_min", 0))
        y_min = int(bbox.get("y_min", 0))
        x_max = int(bbox.get("x_max", frame.shape[1]))
        y_max = int(bbox.get("y_max", frame.shape[0]))

        # Crop the region of interest from the frame (OpenCV BGR)
        import cv2
        cropped = frame[y_min:y_max, x_min:x_max]

        # Encode to JPEG
        _, encoded_img = cv2.imencode(".jpg", cropped)
        img_bytes = encoded_img.tobytes()
        b64_data = base64.b64encode(img_bytes).decode("utf-8")

        return b64_data, "image/jpeg"

    def analyze_threat(self, frame: bytes, bbox: dict, person_description: str = "") -> Optional[dict]:
        """Send a cropped person image to Qwen-VL for threat assessment.

        Args:
            frame: Full frame as numpy array bytes (or raw JPEG).
            bbox: Bounding box with x_min, y_min, x_max, y_max.
            person_description: Optional prior description of the person.

        Returns:
            Dict with threat_level, description, confidence, detected_objects.
        """
        if not self.api_key or self.api_key == "your-dashscope-api-key-here":
            logger.warning("Qwen API key not configured. Returning mock analysis.")
            return self._mock_analysis(person_description)

        try:
            # Encode the cropped region
            b64_img, mime_type = self._encode_image_for_qwen(frame, bbox)

            user_content = {
                "text": f"{self.THREAT_ASSESSMENT_PROMPT}\n\nAdditional context: {person_description or 'No prior description available.'}"
            }
            image_content = {
                "image": f"data:{mime_type};base64,{b64_img}",
                "text": "This is the cropped region of the detected person."
            }

            # Build API request payload for Dashscope Qwen-VL
            payload = {
                "model": self.model,
                "input": {
                    "messages": [
                        {
                            "role": "user",
                            "content": [image_content, user_content]
                        }
                    ]
                },
                "parameters": {
                    "top_p": 0.7,
                    "temperature": 0.1
                }
            }

            # Make API call (implementation depends on HTTP library)
            response = self._call_qwen_api(payload)
            return self._parse_response(response)

        except Exception as e:
            logger.error(f"Qwen API call failed: {e}")
            return self._mock_analysis(person_description)

    def _call_qwen_api(self, payload: dict) -> dict:
        """Make HTTP request to Dashscope Qwen-VL API."""
        import urllib.request

        url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-DashScope-WorkFlow": "true"
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")

        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))

    def _parse_response(self, api_response: dict) -> Optional[dict]:
        """Parse Qwen-VL API response into our internal format."""
        try:
            # Dashscope returns output in a specific structure
            choices = api_response.get("output", {}).get("choices", [])
            if not choices:
                return None

            message = choices[0].get("message", {})
            content = message.get("content", [])

            # Extract text response
            text_response = ""
            for item in content:
                if isinstance(item, dict) and "text" in item:
                    text_response += item["text"] + "\n"

            if not text_response.strip():
                return None

            # Parse the AI's analysis to extract structured data
            # This is a simplified extraction - in production, you'd use more robust parsing
            threat_level = self._extract_threat_level(text_response)
            confidence = self._estimate_confidence(text_response)
            detected_objects = self._extract_detected_objects(text_response)

            return {
                "threat_level": threat_level,
                "description": text_response.strip()[:500],  # Truncate long responses
                "confidence": confidence,
                "detected_objects": detected_objects,
                "is_familiar": False
            }

        except Exception as e:
            logger.error(f"Failed to parse Qwen response: {e}")
            return None

    def _extract_threat_level(self, text: str) -> str:
        """Extract threat level from AI response text."""
        text_lower = text.lower()
        if "high" in text_lower and ("threat" in text_lower or "danger" in text_lower):
            return "threat"
        elif "medium" in text_lower:
            return "unknown"
        else:
            return "safe"

    def _estimate_confidence(self, text: str) -> float:
        """Estimate confidence from AI response (simplified)."""
        # Look for explicit confidence mentions
        import re
        match = re.search(r"confidence[:\s]+(\d+\.?\d*)", text.lower())
        if match:
            return min(float(match.group(1)), 1.0)
        # Default moderate confidence
        return 0.75

    def _extract_detected_objects(self, text: str) -> list[str]:
        """Extract detected object names from AI response."""
        import re
        objects = []
        common_security_relevant = ["weapon", "gun", "knife", "package", "bag",
                                     "uniform", "vehicle", "phone", "tools"]

        for obj in common_security_relevant:
            if obj in text.lower():
                objects.append(obj)

        return objects

    def _mock_analysis(self, person_description: str = "") -> dict:
        """Return mock analysis when API is not configured.

        This ensures the system works during development and testing.
        """
        import random

        # Simple heuristic based on description keywords
        desc_lower = person_description.lower() if person_description else ""

        threat_keywords = ["weapon", "gun", "knife", "aggressive", "threat", "armed"]
        safe_keywords = ["uniform", "package", "delivery", "police", "neighbor", "familiar"]

        threat_score = sum(1 for kw in threat_keywords if kw in desc_lower)
        safe_score = sum(1 for kw in safe_keywords if kw in desc_lower)

        if threat_score > safe_score:
            status = "threat"
            confidence = 0.7 + (threat_score * 0.05)
        elif safe_score > threat_score:
            status = "safe"
            confidence = 0.6 + (safe_score * 0.05)
        else:
            status = random.choice(["threat", "safe", "unknown"])
            confidence = 0.5

        return {
            "threat_level": status,
            "description": f"Mock analysis: {person_description or 'No description available'}",
            "confidence": min(confidence, 0.95),
            "detected_objects": ["person"],
            "is_familiar": False
        }

    def analyze_frame_for_persons(self, frame, detections: list[dict]) -> list[dict]:
        """Analyze all detected persons in a frame using Qwen-VL.

        Args:
            frame: Full frame as numpy array (OpenCV BGR).
            detections: List of YOLO detection dicts.

        Returns:
            List of enriched detection results with Qwen analysis.
        """
        results = []
        for det in detections:
            if det["class_name"] == "person":
                qwen_result = self.analyze_threat(frame, det)
                enriched = dict(det)
                if qwen_result:
                    enriched.update(qwen_result)
                results.append(enriched)

        return results