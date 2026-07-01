"""Pydantic schemas for request/response validation."""

from pydantic import BaseModel, Field
from typing import Optional


class DetectionResult(BaseModel):
    """Single object detection result from YOLO."""
    class_name: str
    confidence: float
    x_min: int
    y_min: int
    x_max: int
    y_max: int


class AnalyzeFrameRequest(BaseModel):
    """Request body for frame analysis."""
    frame_data: str = Field(..., description="Base64 encoded image frame")
    timestamp: Optional[str] = None
    gps: Optional[dict] = None


class QwenAnalysisResponse(BaseModel):
    """Semantic analysis result from Qwen Cloud."""
    threat_level: str  # "threat", "safe", "unknown"
    description: str
    confidence: float
    detected_objects: list[str]
    is_familiar: bool = False
    familiar_name: Optional[str] = None


class AnalysisResponse(BaseModel):
    """Combined response sent back to mobile app."""
    status: str  # "threat" | "safe" | "unknown"
    confidence: float
    message: str
    detections: list[DetectionResult] = []
    qwen_analysis: Optional[QwenAnalysisResponse] = None


class FamiliarFaceRequest(BaseModel):
    """Register a person as familiar/safe."""
    name: str
    image_description: str