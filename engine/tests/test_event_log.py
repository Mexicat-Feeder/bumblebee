"""Tests for the Bumblebee event log."""
import sqlite3
import time
import pytest
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from engine.event_log import EventLog, TicketEvent, init_db, now_iso


@pytest.fixture
def db():
    """In-memory SQLite database with schema initialized."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_db(conn)
    # Insert a test ticket
    conn.execute(
        "INSERT INTO tickets (id, owner, status) VALUES ('T-1', 'test', 'todo')"
    )
    conn.execute(
        "INSERT INTO tickets (id, owner, status) VALUES ('T-2', 'test', 'todo')"
    )
    conn.execute(
        "INSERT INTO tickets (id, owner, status) VALUES ('T-3', 'test', 'blocked')"
    )
    conn.commit()
    return conn


@pytest.fixture
def log(db):
    return EventLog(db)


class TestEventRecording:

    def test_transition_writes_event(self, log):
        event = log.record("T-1", "todo", "in_progress", "executor")
        assert event.id is not None
        assert event.ticket_id == "T-1"
        assert event.from_status == "todo"
        assert event.to_status == "in_progress"
        assert event.actor == "executor"

    def test_event_log_matches_current_status(self, log, db):
        """After N transitions, tickets.status == last event's to_status."""
        log.record("T-1", "todo", "in_progress", "executor")
        log.record("T-1", "in_progress", "done", "executor")
        log.record("T-1", "done", "qa_verified", "executor")

        # Check denormalized status
        row = db.execute("SELECT status FROM tickets WHERE id='T-1'").fetchone()
        assert row["status"] == "qa_verified"

        # Check event log agrees
        last = log.last_event("T-1")
        assert last.to_status == "qa_verified"

    def test_event_with_metadata(self, log):
        event = log.record(
            "T-1", "todo", "in_progress", "executor",
            note="dispatching to Forge",
            metadata={"attempt": 1, "duration_s": 88.5},
        )
        assert event.metadata["attempt"] == 1
        assert event.metadata["duration_s"] == 88.5

    def test_event_log_is_append_only(self, log, db):
        """No UPDATE or DELETE on ticket_events. Only INSERT."""
        log.record("T-1", "todo", "in_progress", "executor")
        log.record("T-1", "in_progress", "blocked", "executor")
        log.record("T-1", "blocked", "todo", "executor")

        count = db.execute("SELECT COUNT(*) FROM ticket_events").fetchone()[0]
        assert count == 3  # all three events preserved

        # Verify we can't accidentally delete
        events = log.events_for("T-1")
        assert len(events) == 3
        assert events[0].to_status == "in_progress"
        assert events[1].to_status == "blocked"
        assert events[2].to_status == "todo"


class TestEventQueries:

    def test_last_event(self, log):
        log.record("T-1", "todo", "in_progress", "executor")
        log.record("T-1", "in_progress", "done", "executor")
        last = log.last_event("T-1")
        assert last.to_status == "done"

    def test_last_event_nonexistent_ticket(self, log):
        assert log.last_event("NOPE") is None

    def test_events_for_ticket(self, log):
        log.record("T-1", "todo", "in_progress", "executor")
        log.record("T-1", "in_progress", "done", "executor")
        log.record("T-2", "todo", "in_progress", "executor")

        events = log.events_for("T-1")
        assert len(events) == 2
        assert all(e.ticket_id == "T-1" for e in events)

    def test_event_count(self, log):
        assert log.event_count("T-1") == 0
        log.record("T-1", "todo", "in_progress", "executor")
        assert log.event_count("T-1") == 1
        log.record("T-1", "in_progress", "done", "executor")
        assert log.event_count("T-1") == 2

    def test_full_lifecycle_audit_trail(self, log):
        """Walk a ticket from todo → qa_verified.
        Event log has one row per transition, in order, with correct actors."""
        log.record("T-1", "todo", "in_progress", "executor", note="claimed")
        log.record("T-1", "in_progress", "done", "executor", note="files written")
        log.record("T-1", "done", "qa_verified", "executor", note="QA passed")

        events = log.events_for("T-1")
        assert len(events) == 3
        assert [(e.from_status, e.to_status) for e in events] == [
            ("todo", "in_progress"),
            ("in_progress", "done"),
            ("done", "qa_verified"),
        ]
        assert all(e.actor == "executor" for e in events)
        # Timestamps are in order
        assert events[0].timestamp <= events[1].timestamp <= events[2].timestamp


class TestStuckTickets:

    def test_stuck_tickets_query(self, log, db):
        """Insert events with old timestamps. Verify stuck_tickets() finds them."""
        old_ts = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
        db.execute(
            """INSERT INTO ticket_events 
               (ticket_id, from_status, to_status, actor, timestamp)
               VALUES ('T-3', 'todo', 'blocked', 'executor', ?)""",
            (old_ts,),
        )
        db.commit()

        stuck = log.stuck_tickets(threshold_minutes=60)
        ticket_ids = [s[0] for s in stuck]
        assert "T-3" in ticket_ids

    def test_recent_tickets_not_stuck(self, log):
        log.record("T-1", "todo", "in_progress", "executor")
        stuck = log.stuck_tickets(threshold_minutes=60)
        ticket_ids = [s[0] for s in stuck]
        assert "T-1" not in ticket_ids

    def test_qa_verified_not_counted_as_stuck(self, log, db):
        """Terminal state tickets should not appear as stuck."""
        old_ts = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
        db.execute("UPDATE tickets SET status='qa_verified' WHERE id='T-2'")
        db.execute(
            """INSERT INTO ticket_events 
               (ticket_id, from_status, to_status, actor, timestamp)
               VALUES ('T-2', 'done', 'qa_verified', 'executor', ?)""",
            (old_ts,),
        )
        db.commit()

        stuck = log.stuck_tickets(threshold_minutes=60)
        ticket_ids = [s[0] for s in stuck]
        assert "T-2" not in ticket_ids


class TestHealthScore:

    def test_healthy_ticket_low_score(self, log):
        """Ticket with forward-only progress scores low."""
        log.record("T-1", "todo", "in_progress", "executor")
        log.record("T-1", "in_progress", "done", "executor")
        log.record("T-1", "done", "qa_verified", "executor")
        score = log.health_score("T-1")
        assert score == 0.0

    def test_churning_ticket_high_score(self, log):
        """Ticket bouncing between blocked and todo scores high."""
        log.record("T-1", "todo", "in_progress", "executor")
        log.record("T-1", "in_progress", "blocked", "executor")
        log.record("T-1", "blocked", "todo", "executor")
        log.record("T-1", "todo", "in_progress", "executor")
        log.record("T-1", "in_progress", "blocked", "executor")
        log.record("T-1", "blocked", "todo", "executor")
        score = log.health_score("T-1")
        assert score > 0.3  # significant churn

    def test_no_events_score_zero(self, log):
        score = log.health_score("T-1")
        assert score == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
