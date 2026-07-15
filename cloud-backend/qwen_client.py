"""
Thin client around Qwen-VL via the Qwen Cloud API (OpenAI-compatible SDK).

API base: https://dashscope-intl.aliyuncs.com/compatible-mode/v1
Auth: QWEN_API_KEY env var (from the hackathon voucher / free trial).
"""
import base64
import json
import logging
import os
import re

from openai import OpenAI

logger = logging.getLogger(__name__)

client = OpenAI(
    api_key=os.environ.get("QWEN_API_KEY"),
    base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
)

QWEN_VL_MODEL = os.environ.get("QWEN_VL_MODEL", "qwen-vl-plus")
VALID_CLASSIFICATIONS = {"familiar", "delivery-like", "anomalous"}

CLASSIFICATION_PROMPT = """You are a home security context assistant. Given an
image of a person near a front door/entrance, classify them as one of:
"familiar", "delivery-like", or "anomalous". Give one short, plain-language
sentence explaining why. Do not speculate about weapons or make safety
claims — describe only what is visibly relevant to context (attire, posture,
carried items, apparent purpose). Respond as JSON: {"classification": "...",
"reasoning": "..."}."""


def classify_frame(frame_bytes: bytes) -> dict:
    """
    Send frame_bytes to Qwen-VL for visitor-context classification.

    Returns {"classification": "familiar"|"delivery-like"|"anomalous",
    "reasoning": "..."}. Falls back to a conservative "anomalous" result if
    the API call fails or the response isn't parseable — an over-cautious
    alert beats silently dropping a visit (system informs, never acts; see
    CLAUDE.md).
    """
    encoded = base64.b64encode(frame_bytes).decode("utf-8")
    data_url = f"data:image/jpeg;base64,{encoded}"

    try:
        response = client.chat.completions.create(
            model=QWEN_VL_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": CLASSIFICATION_PROMPT},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                }
            ],
        )
    except Exception as exc:
        logger.error("Qwen-VL request failed: %s", exc)
        return _fallback_result(f"Qwen-VL request failed: {exc}")

    content = response.choices[0].message.content or ""
    result = _parse_classification(content)
    if result is None:
        logger.error("Qwen-VL returned an unparseable response: %r", content)
        return _fallback_result("Qwen-VL response could not be parsed.")

    return result


def _parse_classification(content: str) -> dict | None:
    """Extract {"classification", "reasoning"} from a Qwen-VL text response,
    tolerating markdown code fences or stray text around the JSON object."""
    match = re.search(r"\{.*\}", content, re.DOTALL)
    if not match:
        return None

    try:
        parsed = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None

    classification = parsed.get("classification")
    reasoning = parsed.get("reasoning")
    if classification not in VALID_CLASSIFICATIONS or not reasoning:
        return None

    return {"classification": classification, "reasoning": reasoning}


def _fallback_result(reason: str) -> dict:
    return {"classification": "anomalous", "reasoning": reason}
