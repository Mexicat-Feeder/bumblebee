"""
research_db.py — Standalone research database schema and initialization.

This module initializes a research-specific SQLite database that is separate
from project tickets.db files. It reuses the same tickets/ticket_requirements/
ticket_events schema as the main engine, plus adds a research_queue table.
"""
from __future__ import annotations

import sqlite3

from .event_log import (
    TICKET_EVENTS_SCHEMA,
    TICKET_REQUIREMENTS_SCHEMA,
    TICKETS_SCHEMA,
)

RESEARCH_QUEUE_SCHEMA = """
CREATE TABLE IF NOT EXISTS research_queue (
    ticket_id TEXT PRIMARY KEY,
    requested_by TEXT DEFAULT 'dashboard',
    consumed_by TEXT DEFAULT 'sift',
    closure_mode TEXT DEFAULT 'auto',
    queue_status TEXT DEFAULT 'queued',
    priority INTEGER DEFAULT 5,
    brief_path TEXT,
    report_path TEXT,
    review_path TEXT,
    enqueued_at TEXT,
    last_attempt_at TEXT,
    last_note TEXT DEFAULT '',
    attempt_count INTEGER DEFAULT 0,
    FOREIGN KEY (ticket_id) REFERENCES tickets(id)
);
CREATE INDEX IF NOT EXISTS idx_research_queue_status ON research_queue(queue_status);
CREATE INDEX IF NOT EXISTS idx_research_queue_priority ON research_queue(priority, enqueued_at);
"""


def init_research_db(conn: sqlite3.Connection) -> None:
    """Initialize all tables needed for the research database."""
    conn.executescript(TICKETS_SCHEMA)
    conn.executescript(TICKET_REQUIREMENTS_SCHEMA)
    conn.executescript(TICKET_EVENTS_SCHEMA)
    conn.executescript(RESEARCH_QUEUE_SCHEMA)
    conn.commit()
