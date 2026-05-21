"""
Swarm Engine — Event Log

Append-only event log for ticket state transitions.
Every state change writes a row. The tickets.status column is a
denormalized cache — the event log is the source of truth.
"""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class TicketEvent:
    """A single recorded state transition event."""
    id: int | None
    ticket_id: str
    from_status: str | None
    to_status: str
    actor: str
    timestamp: str
    note: str | None = None
    metadata_json: str | None = None

    @property
    def metadata(self) -> dict[str, Any]:
        if self.metadata_json:
            try:
                return json.loads(self.metadata_json)
            except (json.JSONDecodeError, TypeError):
                return {}
        return {}


# ── Schema ────────────────────────────────────────────────────────

TICKET_EVENTS_SCHEMA = """
CREATE TABLE IF NOT EXISTS ticket_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id TEXT NOT NULL,
    from_status TEXT,
    to_status TEXT NOT NULL,
    actor TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    note TEXT,
    metadata_json TEXT
);
CREATE INDEX IF NOT EXISTS idx_ticket_events_ticket_id ON ticket_events(ticket_id);
CREATE INDEX IF NOT EXISTS idx_ticket_events_timestamp ON ticket_events(timestamp);
"""

TICKETS_SCHEMA = """
CREATE TABLE IF NOT EXISTS tickets (
    id TEXT PRIMARY KEY,
    owner TEXT,
    gate INTEGER DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'todo',
    blocked_reason_code TEXT,
    assignee TEXT,
    failure_count INTEGER DEFAULT 0,
    attempt_count INTEGER DEFAULT 0,
    depends_on TEXT DEFAULT '[]',
    parent_ticket_id TEXT,
    updated_at TEXT,
    metadata_json TEXT
);
"""

TICKET_REQUIREMENTS_SCHEMA = """
CREATE TABLE IF NOT EXISTS ticket_requirements (
    ticket_id TEXT PRIMARY KEY,
    ticket_description TEXT,
    worker_done_criteria TEXT,
    qa_done_criteria TEXT,
    worker_cmd_json TEXT DEFAULT '[]',
    qa_cmd_json TEXT DEFAULT '[]',
    worker_evidence_json TEXT DEFAULT '[]',
    qa_evidence_json TEXT DEFAULT '[]',
    required_output_files_json TEXT DEFAULT '[]',
    interaction_spec TEXT,
    ui_check_spec TEXT,
    constraints_json TEXT DEFAULT '[]',
    context_files_json TEXT DEFAULT '[]',
    enforce INTEGER DEFAULT 1,
    requires_live_review INTEGER DEFAULT 0,
    integration_check_cmd_json TEXT DEFAULT '[]',
    updated_at TEXT,
    FOREIGN KEY (ticket_id) REFERENCES tickets(id)
);
"""


def init_db(conn: sqlite3.Connection) -> None:
    """Initialize all tables."""
    conn.executescript(TICKET_EVENTS_SCHEMA)
    conn.executescript(TICKETS_SCHEMA)
    conn.executescript(TICKET_REQUIREMENTS_SCHEMA)
    conn.commit()


# ── Event log operations ──────────────────────────────────────────

class EventLog:
    """Append-only event log for ticket state transitions."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def record(
        self,
        ticket_id: str,
        from_status: str | None,
        to_status: str,
        actor: str,
        note: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> TicketEvent:
        """Record a state transition event. Append-only."""
        ts = now_iso()
        meta_json = json.dumps(metadata) if metadata else None
        cursor = self.conn.execute(
            """INSERT INTO ticket_events 
               (ticket_id, from_status, to_status, actor, timestamp, note, metadata_json)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (ticket_id, from_status, to_status, actor, ts, note, meta_json),
        )
        # Update denormalized status on tickets table
        self.conn.execute(
            "UPDATE tickets SET status=?, updated_at=? WHERE id=?",
            (to_status, ts, ticket_id),
        )
        self.conn.commit()
        return TicketEvent(
            id=cursor.lastrowid,
            ticket_id=ticket_id,
            from_status=from_status,
            to_status=to_status,
            actor=actor,
            timestamp=ts,
            note=note,
            metadata_json=meta_json,
        )

    def last_event(self, ticket_id: str) -> TicketEvent | None:
        """Get the most recent event for a ticket."""
        row = self.conn.execute(
            """SELECT id, ticket_id, from_status, to_status, actor, timestamp, note, metadata_json
               FROM ticket_events WHERE ticket_id=? ORDER BY id DESC LIMIT 1""",
            (ticket_id,),
        ).fetchone()
        if not row:
            return None
        return TicketEvent(*row)

    def events_for(self, ticket_id: str) -> list[TicketEvent]:
        """Get all events for a ticket, oldest first."""
        rows = self.conn.execute(
            """SELECT id, ticket_id, from_status, to_status, actor, timestamp, note, metadata_json
               FROM ticket_events WHERE ticket_id=? ORDER BY id ASC""",
            (ticket_id,),
        ).fetchall()
        return [TicketEvent(*r) for r in rows]

    def events_since(self, ticket_id: str, minutes: int) -> list[TicketEvent]:
        """Get events for a ticket in the last N minutes."""
        cutoff = datetime.now(timezone.utc).isoformat()
        # Simple approach: fetch all and filter (events are small)
        all_events = self.events_for(ticket_id)
        cutoff_dt = datetime.now(timezone.utc)
        result = []
        for e in all_events:
            try:
                evt_dt = datetime.fromisoformat(e.timestamp)
                if evt_dt.tzinfo is None:
                    evt_dt = evt_dt.replace(tzinfo=timezone.utc)
                diff = (cutoff_dt - evt_dt).total_seconds()
                if diff <= minutes * 60:
                    result.append(e)
            except (ValueError, TypeError):
                pass
        return result

    def stuck_tickets(self, threshold_minutes: int) -> list[tuple[str, str, float]]:
        """Find tickets whose last event is older than threshold.
        Returns list of (ticket_id, last_status, minutes_since_last_event)."""
        rows = self.conn.execute(
            """SELECT te.ticket_id, te.to_status, te.timestamp
               FROM ticket_events te
               INNER JOIN (
                   SELECT ticket_id, MAX(id) as max_id
                   FROM ticket_events GROUP BY ticket_id
               ) latest ON te.id = latest.max_id
               JOIN tickets t ON t.id = te.ticket_id
               WHERE t.status NOT IN ('qa_verified')""",
        ).fetchall()
        now = datetime.now(timezone.utc)
        stuck = []
        for ticket_id, status, ts in rows:
            try:
                evt_dt = datetime.fromisoformat(ts)
                if evt_dt.tzinfo is None:
                    evt_dt = evt_dt.replace(tzinfo=timezone.utc)
                minutes = (now - evt_dt).total_seconds() / 60
                if minutes >= threshold_minutes:
                    stuck.append((ticket_id, status, minutes))
            except (ValueError, TypeError):
                pass
        return stuck

    def health_score(self, ticket_id: str, window: int = 10) -> float:
        """Score ticket health based on recent event patterns.
        Lower = healthier. Higher = more churn.
        Score = count of non-forward transitions in last N events."""
        events = self.events_for(ticket_id)[-window:]
        if not events:
            return 0.0

        forward_states = ["todo", "in_progress", "done", "qa_verified"]
        non_forward = 0
        for e in events:
            if e.to_status == "blocked" or (
                e.from_status and e.to_status and
                forward_states.index(e.to_status) <= forward_states.index(e.from_status)
                if e.from_status in forward_states and e.to_status in forward_states
                else False
            ):
                non_forward += 1
        return non_forward / len(events)

    def event_count(self, ticket_id: str) -> int:
        """Total number of events for a ticket."""
        row = self.conn.execute(
            "SELECT COUNT(*) FROM ticket_events WHERE ticket_id=?",
            (ticket_id,),
        ).fetchone()
        return row[0] if row else 0
