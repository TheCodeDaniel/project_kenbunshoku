"""
Lightweight visit history / pattern store. SQLite for MVP simplicity; swap for
Redis if concurrent-access needs grow.

Schema (visits table):
  id, camera_id, timestamp, classification, reasoning

Pattern logic (MVP-simple, not ML): if the same camera_id has seen a similar
classification at a similar time-of-day window N+ times in the recent window,
treat it as a "recognized pattern" rather than a fresh unfamiliar visit.
"""
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Optional

DB_PATH = "kenbunshoku_memory.db"

RECENT_WINDOW_DAYS = 14  # how far back to look for recurring visits
TIME_OF_DAY_WINDOW_HOURS = 1.5  # how close two visits' times-of-day must be to count as "similar"
PATTERN_MIN_COUNT = 2  # occurrences (including this visit) needed to call it a recognized pattern


@contextmanager
def _conn():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with _conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS visits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                camera_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                classification TEXT NOT NULL,
                reasoning TEXT
            )
        """)


def record_visit(camera_id: str, timestamp: str, classification: str, reasoning: str) -> None:
    """Insert a visit row."""
    with _conn() as conn:
        conn.execute(
            "INSERT INTO visits (camera_id, timestamp, classification, reasoning) VALUES (?, ?, ?, ?)",
            (camera_id, timestamp, classification, reasoning),
        )


def get_pattern_context(camera_id: str, classification: str, timestamp: str) -> str:
    """
    Look at this camera's recent visits with the same classification and, if
    enough of them cluster around the same time-of-day as `timestamp`,
    return a short context string like "3rd similar visit in the last 14
    days, usual time window (~09:15)". Returns "" if no pattern is found.
    """
    current = _parse_timestamp(timestamp)
    if current is None:
        return ""

    window_start = current - timedelta(days=RECENT_WINDOW_DAYS)

    with _conn() as conn:
        rows = conn.execute(
            "SELECT timestamp FROM visits WHERE camera_id = ? AND classification = ?",
            (camera_id, classification),
        ).fetchall()

    matches = 0
    for (row_timestamp,) in rows:
        visit_time = _parse_timestamp(row_timestamp)
        if visit_time is None or not (window_start <= visit_time <= current):
            continue
        if _same_time_of_day(visit_time, current):
            matches += 1

    total_occurrences = matches + 1  # including this visit
    if total_occurrences < PATTERN_MIN_COUNT:
        return ""

    return (
        f"{_ordinal(total_occurrences)} similar visit in the last {RECENT_WINDOW_DAYS} days, "
        f"usual time window (~{current.strftime('%H:%M')})"
    )


def _parse_timestamp(value: str) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def _same_time_of_day(
    a: datetime, b: datetime, window_hours: float = TIME_OF_DAY_WINDOW_HOURS
) -> bool:
    minutes_a = a.hour * 60 + a.minute
    minutes_b = b.hour * 60 + b.minute
    diff = abs(minutes_a - minutes_b)
    diff = min(diff, 24 * 60 - diff)  # wrap around midnight
    return diff <= window_hours * 60


def _ordinal(n: int) -> str:
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"
