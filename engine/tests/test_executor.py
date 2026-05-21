"""Tests for the single-cycle sequential executor."""
import json
import sqlite3
import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from engine.state_machine import StateMachine, TicketState
from engine.event_log import EventLog, init_db, now_iso
from engine.config import ProjectConfig, UICheckConfig
from engine.executor import Executor, CycleResult, cleanup_child_processes, _tracked_pids


# ── Fixtures ──────────────────────────────────────────────────────

@pytest.fixture
def db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_db(conn)
    return conn


@pytest.fixture
def config(tmp_path):
    return ProjectConfig(
        engine_root=tmp_path / "engine",
        project_root=tmp_path / "project",
        workspace_root=tmp_path,
        deliverable_root=tmp_path / "deliver",
        db_path=tmp_path / "tickets.db",
        artifacts_dir=tmp_path / "deliver" / "artifacts",
        checks_dir=tmp_path / "deliver" / "checks",
        qa_reports_dir=tmp_path / "deliver" / "reports",
        forge_agent="forge",
        models={"forge": "test/model", "vision": "test/model"},
        forge_timeout_seconds=60,
        cycle_interval_seconds=0,  # no sleep in tests
        max_dispatch_attempts=3,
    )


def _insert_ticket(conn, ticket_id, status="todo", gate=1, depends_on="[]",
                    parent_ticket_id=None, blocked_reason_code=None, assignee=None,
                    failure_count=0, attempt_count=0):
    conn.execute(
        """INSERT INTO tickets (id, owner, gate, status, depends_on, parent_ticket_id,
           blocked_reason_code, assignee, failure_count, attempt_count, updated_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (ticket_id, "test", gate, status, depends_on, parent_ticket_id,
         blocked_reason_code, assignee, failure_count, attempt_count, now_iso()),
    )
    conn.execute(
        """INSERT INTO ticket_requirements (ticket_id, ticket_description, required_output_files_json)
           VALUES (?, ?, ?)""",
        (ticket_id, f"Test ticket {ticket_id}", '["src/test.ts"]'),
    )
    conn.commit()


def make_executor(db, config, dispatch_fn=None, qa_fn=None):
    sm = StateMachine()
    event_log = EventLog(db)
    return Executor(
        config=config,
        state_machine=sm,
        conn=db,
        event_log=event_log,
        dispatch_fn=dispatch_fn,
        qa_fn=qa_fn,
    )


# ── Route tests ───────────────────────────────────────────────────

class TestRouting:

    def test_single_cycle_advances_ready_ticket(self, db, config):
        _insert_ticket(db, "T-1")
        ex = make_executor(db, config)
        count = ex.route_ready_tickets()
        assert count == 1
        row = db.execute("SELECT status FROM tickets WHERE id='T-1'").fetchone()
        assert row["status"] == "in_progress"

    def test_ticket_with_unmet_deps_stays_todo(self, db, config):
        _insert_ticket(db, "T-DEP", status="todo")  # dep not done
        _insert_ticket(db, "T-1", depends_on='["T-DEP"]')
        ex = make_executor(db, config)
        count = ex.route_ready_tickets()
        # T-DEP should advance, T-1 should not (dep not qa_verified)
        row = db.execute("SELECT status FROM tickets WHERE id='T-1'").fetchone()
        assert row["status"] == "todo"

    def test_blocked_retry_routes_back_to_todo(self, db, config):
        _insert_ticket(db, "T-1", status="blocked", blocked_reason_code="timeout",
                       attempt_count=0)
        ex = make_executor(db, config)
        count = ex.route_ready_tickets()
        assert count >= 1
        row = db.execute("SELECT status FROM tickets WHERE id='T-1'").fetchone()
        assert row["status"] == "todo"

    def test_blocked_children_complete_unblocks_parent(self, db, config):
        _insert_ticket(db, "T-P", status="blocked",
                       blocked_reason_code="waiting_on_child_packets")
        _insert_ticket(db, "T-C1", status="qa_verified", parent_ticket_id="T-P")
        _insert_ticket(db, "T-C2", status="qa_verified", parent_ticket_id="T-P")
        ex = make_executor(db, config)
        count = ex.route_ready_tickets()
        row = db.execute("SELECT status FROM tickets WHERE id='T-P'").fetchone()
        assert row["status"] == "todo"


# ── Dispatch tests ────────────────────────────────────────────────

class TestDispatch:

    def test_dispatch_calls_dispatch_fn(self, db, config):
        _insert_ticket(db, "T-1", status="in_progress", assignee="executor")
        calls = []
        def mock_dispatch(tid, cfg):
            calls.append(tid)
            return True, "files written"

        ex = make_executor(db, config, dispatch_fn=mock_dispatch)
        result = ex.dispatch_next()
        assert result == "T-1"
        assert calls == ["T-1"]

    def test_dispatch_success_moves_to_done(self, db, config):
        _insert_ticket(db, "T-1", status="in_progress", assignee="executor")
        ex = make_executor(db, config, dispatch_fn=lambda tid, cfg: (True, "ok"))
        ex.dispatch_next()
        row = db.execute("SELECT status FROM tickets WHERE id='T-1'").fetchone()
        assert row["status"] == "done"

    def test_dispatch_failure_moves_to_blocked(self, db, config):
        _insert_ticket(db, "T-1", status="in_progress", assignee="executor")
        ex = make_executor(db, config, dispatch_fn=lambda tid, cfg: (False, "tsc failed"))
        ex.dispatch_next()
        row = db.execute("SELECT status, blocked_reason_code FROM tickets WHERE id='T-1'").fetchone()
        assert row["status"] == "blocked"
        assert row["blocked_reason_code"] == "execution_failure"

    def test_parent_with_pending_children_blocks(self, db, config):
        _insert_ticket(db, "T-P", status="in_progress", assignee="executor")
        _insert_ticket(db, "T-C1", status="todo", parent_ticket_id="T-P")
        ex = make_executor(db, config)
        result = ex.dispatch_next()
        assert result is None  # parent blocked, not dispatched
        row = db.execute("SELECT status FROM tickets WHERE id='T-P'").fetchone()
        assert row["status"] == "blocked"
        row2 = db.execute("SELECT blocked_reason_code FROM tickets WHERE id='T-P'").fetchone()
        assert row2["blocked_reason_code"] == "waiting_on_child_packets"

    def test_no_dispatch_when_nothing_in_progress(self, db, config):
        _insert_ticket(db, "T-1", status="todo")
        ex = make_executor(db, config)
        result = ex.dispatch_next()
        assert result is None


# ── QA tests ──────────────────────────────────────────────────────

class TestQA:

    def test_qa_pass_moves_to_qa_verified(self, db, config):
        _insert_ticket(db, "T-1", status="done")
        ex = make_executor(db, config, qa_fn=lambda tid, cfg: (True, "all checks pass"))
        count = ex.verify_done_tickets()
        assert count == 1
        row = db.execute("SELECT status FROM tickets WHERE id='T-1'").fetchone()
        assert row["status"] == "qa_verified"

    def test_qa_fail_moves_to_blocked(self, db, config):
        _insert_ticket(db, "T-1", status="done")
        ex = make_executor(db, config, qa_fn=lambda tid, cfg: (False, "file missing"))
        count = ex.verify_done_tickets()
        row = db.execute("SELECT status, blocked_reason_code FROM tickets WHERE id='T-1'").fetchone()
        assert row["status"] == "blocked"
        assert row["blocked_reason_code"] == "qa_failure"


# ── Full cycle tests ──────────────────────────────────────────────

class TestFullCycle:

    def test_full_cycle_routes_dispatches_verifies(self, db, config):
        _insert_ticket(db, "T-1", status="todo")
        ex = make_executor(
            db, config,
            dispatch_fn=lambda tid, cfg: (True, "ok"),
            qa_fn=lambda tid, cfg: (True, "pass"),
        )
        r = ex.run_cycle(1)
        assert r.tickets_routed >= 1
        # After route + dispatch + verify in one cycle:
        # T-1: todo → in_progress (route) → done (dispatch) → qa_verified (verify)
        row = db.execute("SELECT status FROM tickets WHERE id='T-1'").fetchone()
        assert row["status"] == "qa_verified"

    def test_full_10_ticket_simulation(self, db, config):
        """3 parents with children. Mock Forge. Run until all qa_verified."""
        # Gate 0: 2 standalone tickets
        _insert_ticket(db, "G0-A", gate=0)
        _insert_ticket(db, "G0-B", gate=0)

        # Gate 1 parent + 3 children
        _insert_ticket(db, "G1-P", gate=1, depends_on='["G0-A", "G0-B"]')
        _insert_ticket(db, "G1-A", gate=1, depends_on='["G0-A"]', parent_ticket_id="G1-P")
        _insert_ticket(db, "G1-B", gate=1, depends_on='["G0-B"]', parent_ticket_id="G1-P")
        _insert_ticket(db, "G1-C", gate=1, depends_on='["G1-A"]', parent_ticket_id="G1-P")

        # Gate 2 parent + 2 children
        _insert_ticket(db, "G2-P", gate=2, depends_on='["G1-P"]')
        _insert_ticket(db, "G2-A", gate=2, depends_on='["G1-P"]', parent_ticket_id="G2-P")
        _insert_ticket(db, "G2-B", gate=2, depends_on='["G2-A"]', parent_ticket_id="G2-P")

        # Gate 3: standalone
        _insert_ticket(db, "G3-A", gate=3, depends_on='["G2-P"]')

        ex = make_executor(
            db, config,
            dispatch_fn=lambda tid, cfg: (True, f"files written for {tid}"),
            qa_fn=lambda tid, cfg: (True, f"qa pass for {tid}"),
        )

        results = ex.run_loop(max_cycles=50)

        # All tickets should be qa_verified
        rows = db.execute("SELECT id, status FROM tickets ORDER BY id").fetchall()
        statuses = {r["id"]: r["status"] for r in rows}

        for tid, status in statuses.items():
            assert status == "qa_verified", f"{tid} ended in {status}, expected qa_verified"

        # Event log should have entries for every ticket
        event_log = EventLog(db)
        for tid in statuses:
            events = event_log.events_for(tid)
            assert len(events) > 0, f"No events for {tid}"

    def test_executor_terminates_when_stuck(self, db, config):
        """If nothing can advance and nothing is in_progress, executor should stop."""
        _insert_ticket(db, "T-1", status="blocked",
                       blocked_reason_code="pixel_review_required",
                       attempt_count=99)  # not retryable
        ex = make_executor(db, config)
        results = ex.run_loop(max_cycles=5)
        # Should terminate quickly, not loop forever
        assert len(results) <= 2


# ── Process cleanup tests ─────────────────────────────────────────

class TestProcessCleanup:

    def test_cleanup_removes_tracked_pids(self):
        # Track a non-existent PID
        _tracked_pids.add(999999)
        cleanup_child_processes()
        assert 999999 not in _tracked_pids

    def test_cycle_runs_cleanup(self, db, config):
        """Cycle always calls cleanup, even with no work."""
        _insert_ticket(db, "T-1", status="qa_verified")
        ex = make_executor(db, config)
        # Should not raise
        r = ex.run_cycle(1)
        assert r.errors == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
