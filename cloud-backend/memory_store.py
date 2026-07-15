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

DB_PATH = "kenbunshoku_memory.db"


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


def record_visit(camera_id: str, timestamp: str, classification: str, reasoning: str):
    """TODO: insert row."""
    raise NotImplementedError


def get_pattern_context(camera_id: str, classification: str) -> str:
    """
    TODO: query recent visits for this camera_id, compare time-of-day and
    classification, return a short context string like "3rd similar visit
    this week, usual time window" or "" if no pattern found.
    """
    raise NotImplementedError
