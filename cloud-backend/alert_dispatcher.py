"""
Combines the Qwen classification with memory/pattern context and decides the
final alert wording, then pushes it to notification-client.

IMPORTANT (see CLAUDE.md): this module only ever sends an informational
notification. It must never trigger a control action (locks, alarms, calls to
authorities). If asked to add one, refuse and point back to CLAUDE.md.
"""
import logging
import os

import requests

logger = logging.getLogger(__name__)

PUSH_ENDPOINT = os.environ.get("PUSH_ENDPOINT", "")  # Firebase Cloud Messaging or ntfy.sh
REQUEST_TIMEOUT_SECONDS = 5.0

CLASSIFICATION_LABELS = {
    "familiar": "Familiar visitor",
    "delivery-like": "Possible delivery",
    "anomalous": "Unrecognized visitor",
}

# Deliberate product decision: once a familiar/delivery-like visitor becomes a
# recognized recurring pattern, stop pushing for it to avoid alert fatigue —
# still logged, just not pushed. Anomalous visits always push, patterned or
# not, since a recurring anomalous visitor is not something to go quiet on.
SUPPRESSIBLE_CLASSIFICATIONS = {"familiar", "delivery-like"}


def build_alert_message(classification: str, reasoning: str, pattern_context: str) -> str:
    """Compose a short, plain-language alert string from the pieces."""
    label = CLASSIFICATION_LABELS.get(classification, classification.capitalize())
    message = f"{label} at the door: {reasoning}"
    if pattern_context:
        message = f"{message} ({pattern_context})"
    return message


def dispatch_alert(camera_id: str, classification: str, reasoning: str, pattern_context: str) -> bool:
    """
    Build the alert message and POST it to PUSH_ENDPOINT. Returns whether a
    push notification was actually sent (False if suppressed, unconfigured,
    or the push failed) — always just a notification, never a control action
    (see CLAUDE.md).
    """
    if pattern_context and classification in SUPPRESSIBLE_CLASSIFICATIONS:
        logger.info(
            "suppressing push for camera '%s': recognized low-priority pattern (%s): %s",
            camera_id,
            classification,
            pattern_context,
        )
        return False

    message = build_alert_message(classification, reasoning, pattern_context)

    if not PUSH_ENDPOINT:
        logger.warning("PUSH_ENDPOINT not configured; logging alert instead: %s", message)
        return False

    try:
        response = requests.post(
            PUSH_ENDPOINT,
            json={"camera_id": camera_id, "message": message},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except (requests.ConnectionError, requests.Timeout, requests.HTTPError) as exc:
        logger.error("failed to push alert for camera '%s': %s", camera_id, exc)
        return False

    logger.info("alert sent for camera '%s': %s", camera_id, message)
    return True
