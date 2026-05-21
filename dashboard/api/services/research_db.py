"""
research_db.py — read/write research tickets from the old-swarm research DB.
All tickets are RSH-XXX; reports land in SIFT_DIR as RSH-XXX.report.md.
"""
import os
import sqlite3
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

log = logging.getLogger(__name__)

# Map queue_status → display status used by the sidebar colour logic
STATUS_MAP = {
    "queued": "queued",
    "in_progress": "in_progress",
    "delivered": "in_progress",
    "awaiting_human_ack": "awaiting_review",
    "human_acked": "complete",
    "failed": "failed",
}


def _connect(db_path: str) -> sqlite3.Connection:
    # isolation_level=None = autocommit: reads don't start implicit transactions
    # so read connections never block external writers.
    conn = sqlite3.connect(db_path, timeout=20, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=15000")
    return conn


def _next_rsh_id(conn: sqlite3.Connection) -> str:
    rows = conn.execute(
        "SELECT id FROM tickets WHERE id LIKE 'RSH-%' ORDER BY id"
    ).fetchall()
    max_num = 0
    for row in rows:
        try:
            max_num = max(max_num, int(str(row["id"]).split("-", 1)[1]))
        except Exception:
            pass
    return f"RSH-{max_num + 1:03d}"


def list_tickets(db_path: str) -> list[dict]:
    try:
        conn = _connect(db_path)
        rows = conn.execute(
            """
            SELECT
                t.id, t.status AS ticket_status, t.updated_at,
                tr.ticket_description,
                rq.queue_status, rq.priority, rq.report_path,
                rq.enqueued_at, rq.last_note, rq.attempt_count
            FROM tickets t
            LEFT JOIN ticket_requirements tr ON tr.ticket_id = t.id
            LEFT JOIN research_queue rq ON rq.ticket_id = t.id
            WHERE t.id LIKE 'RSH-%'
            ORDER BY rq.priority ASC, rq.enqueued_at DESC
            """
        ).fetchall()
        conn.close()
        result = []
        for r in rows:
            d = dict(r)
            qs = d.get("queue_status") or "queued"
            d["display_status"] = STATUS_MAP.get(qs, qs)
            result.append(d)
        return result
    except Exception as e:
        log.error("list_tickets failed: %s", e)
        return []


def get_ticket(db_path: str, ticket_id: str) -> dict | None:
    try:
        conn = _connect(db_path)
        row = conn.execute(
            """
            SELECT
                t.id, t.status AS ticket_status, t.updated_at,
                tr.ticket_description, tr.worker_done_criteria,
                rq.queue_status, rq.priority, rq.report_path,
                rq.review_path, rq.brief_path,
                rq.enqueued_at, rq.last_attempt_at, rq.last_note, rq.attempt_count
            FROM tickets t
            LEFT JOIN ticket_requirements tr ON tr.ticket_id = t.id
            LEFT JOIN research_queue rq ON rq.ticket_id = t.id
            WHERE t.id = ?
            """,
            (ticket_id,),
        ).fetchone()
        conn.close()
        if not row:
            return None
        d = dict(row)
        qs = d.get("queue_status") or "queued"
        d["display_status"] = STATUS_MAP.get(qs, qs)
        return d
    except Exception as e:
        log.error("get_ticket failed: %s", e)
        return None


def get_report(report_path: str | None) -> str | None:
    """Read the .report.md file. report_path may be absolute or relative to research root."""
    if not report_path:
        return None
    p = Path(report_path)
    if not p.is_absolute():
        return None
    try:
        if p.exists():
            return p.read_text(encoding="utf-8", errors="replace")
        return None
    except Exception as e:
        log.warning("Could not read report at %s: %s", report_path, e)
        return None


def submit_ticket(
    db_path: str,
    research_root: str,
    question: str,
    context: str = "",
    priority: int = 5,
) -> dict:
    """Create a new RSH ticket and enqueue it."""
    conn = _connect(db_path)
    ticket_id = _next_rsh_id(conn)
    now = datetime.now(timezone.utc).isoformat()

    # Build description combining question + context
    description = question.strip()
    if context.strip():
        description += f"\n\nContext:\n{context.strip()}"

    root = Path(research_root)
    # RESEARCH_SIFT_DIR env var overrides; falls back to a "Sift" subdir inside research_root
    sift_dir = Path(os.environ.get("RESEARCH_SIFT_DIR", str(root / "Sift")))
    brief_rel = f"orchestrator/output/research/{ticket_id}.brief.json"
    report_abs = str(sift_dir / f"{ticket_id}.report.md")
    review_rel = f"orchestrator/output/research/{ticket_id}.close.json"

    # Write brief JSON
    brief_path = root / brief_rel
    brief_path.parent.mkdir(parents=True, exist_ok=True)
    brief_path.write_text(
        json.dumps(
            {
                "ticket_id": ticket_id,
                "question": question.strip(),
                "context": context.strip(),
                "enqueued_at": now,
                "requested_by": "dashboard",
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    # Insert into tickets — status must be 'todo' (CHECK constraint in this schema)
    conn.execute(
        """
        INSERT INTO tickets (id, owner, gate, status, depends_on)
        VALUES (?, 'research', 1, 'todo', '[]')
        """,
        (ticket_id,),
    )

    # Insert into ticket_requirements — must supply all NOT NULL columns that have no default
    conn.execute(
        """
        INSERT OR IGNORE INTO ticket_requirements
            (ticket_id, ticket_description, worker_done_criteria, qa_done_criteria)
        VALUES (?, ?, 'Report delivered to Sift directory', 'Human reviewed and acked')
        """,
        (ticket_id, description),
    )

    # Insert into research_queue
    conn.execute(
        """
        INSERT INTO research_queue
            (ticket_id, requested_by, consumed_by, closure_mode, queue_status,
             priority, brief_path, report_path, review_path, enqueued_at, last_note)
        VALUES (?, 'dashboard', 'pixel', 'human_ack', 'queued', ?, ?, ?, ?, ?, '')
        """,
        (ticket_id, priority, brief_rel, report_abs, review_rel, now),
    )

    conn.commit()
    conn.close()
    log.info("Submitted research ticket %s: %s", ticket_id, question[:60])
    return {
        "ticket_id": ticket_id,
        "queue_status": "queued",
        "display_status": "queued",
        "enqueued_at": now,
    }
