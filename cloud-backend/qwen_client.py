"""
Thin client around Qwen-VL via the Qwen Cloud API (OpenAI-compatible SDK).

API base: https://dashscope-intl.aliyuncs.com/compatible-mode/v1
Auth: QWEN_API_KEY env var (from the hackathon voucher / free trial).
"""
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get("QWEN_API_KEY"),
    base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
)

CLASSIFICATION_PROMPT = """You are a home security context assistant. Given an
image of a person near a front door/entrance, classify them as one of:
"familiar", "delivery-like", or "anomalous". Give one short, plain-language
sentence explaining why. Do not speculate about weapons or make safety
claims — describe only what is visibly relevant to context (attire, posture,
carried items, apparent purpose). Respond as JSON: {"classification": "...",
"reasoning": "..."}."""


def classify_frame(frame_bytes: bytes) -> dict:
    """
    TODO: base64-encode frame_bytes, send as an image content block alongside
    CLASSIFICATION_PROMPT to a Qwen-VL model, parse the JSON response.
    """
    raise NotImplementedError
