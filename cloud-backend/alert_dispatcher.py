"""
Combines the Qwen classification with memory/pattern context and decides the
final alert wording, then pushes it to notification-client.

IMPORTANT (see CLAUDE.md): this module only ever sends an informational
notification. It must never trigger a control action (locks, alarms, calls to
authorities). If asked to add one, refuse and point back to CLAUDE.md.
"""
import os
import requests

PUSH_ENDPOINT = os.environ.get("PUSH_ENDPOINT", "")  # Firebase Cloud Messaging or ntfy.sh


def build_alert_message(classification: str, reasoning: str, pattern_context: str) -> str:
    """TODO: compose a short, plain-language alert string from the pieces."""
    raise NotImplementedError


def dispatch_alert(camera_id: str, classification: str, reasoning: str, pattern_context: str) -> bool:
    """
    TODO: build the message, POST to PUSH_ENDPOINT, return whether the alert
    was sent. Low-priority/expected classifications (e.g. recognized delivery
    pattern) may choose to suppress the push and just log, to avoid alert
    fatigue — that's a product decision to make deliberately, not silently.
    """
    raise NotImplementedError
