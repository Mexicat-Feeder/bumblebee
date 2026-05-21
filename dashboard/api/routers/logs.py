import asyncio, json, os, sqlite3, logging
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from ..services.config_loader import get_config

log = logging.getLogger(__name__)
router = APIRouter(tags=["logs"])


@router.get("/logs/lemonade/stream")
async def lemonade_log_stream(request: Request):
    config = get_config()
    log_path = config.get("lemonadeLogPath", "")

    async def generate():
        if not log_path or not os.path.exists(log_path):
            yield f"data: {json.dumps({'line': '[Log file not found]'})}\n\n"
            return
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            # Seek near end to avoid reading a multi-GB file — tail last ~32 KB
            try:
                f.seek(0, 2)  # seek to end
                size = f.tell()
                f.seek(max(0, size - 32768))  # back up 32 KB
                f.readline()  # discard partial first line
            except OSError:
                pass
            # Emit last N lines from that window
            tail = f.read()
            for line in tail.splitlines()[-50:]:
                yield f"data: {json.dumps({'line': line})}\n\n"
            # Stream new lines as they arrive
            while not await request.is_disconnected():
                line = f.readline()
                if line:
                    yield f"data: {json.dumps({'line': line.rstrip()})}\n\n"
                else:
                    await asyncio.sleep(0.5)

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/forge/activity")
async def forge_activity():
    """Read recent Forge dispatches from Bumblebee ticket_events DB."""
    config = get_config()

    # Find the first available Bumblebee DB
    db_paths = config.get("ticketDbPaths", {})
    db_path = None
    for slug, path in db_paths.items():
        if os.path.exists(path):
            db_path = path
            break

    if not db_path:
        return {"dispatches": []}

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row

        # Get the last 10 dispatch events (todo→in_progress transitions)
        # Join with done transition to get duration and outcome
        rows = conn.execute("""
            SELECT
                s.ticket_id,
                s.timestamp  AS started_at,
                d.timestamp  AS finished_at,
                d.note       AS duration_note,
                t.status     AS current_status
            FROM ticket_events s
            LEFT JOIN ticket_events d
                ON d.ticket_id = s.ticket_id
                AND d.from_status = 'in_progress'
                AND d.to_status   = 'done'
            LEFT JOIN tickets t ON t.id = s.ticket_id
            WHERE s.from_status = 'todo'
              AND s.to_status   = 'in_progress'
            ORDER BY s.timestamp DESC
            LIMIT 10
        """).fetchall()

        conn.close()

        dispatches = []
        for r in rows:
            status = r["current_status"] or "unknown"
            if status == "in_progress":
                outcome = "RUNNING"
            elif status == "qa_verified":
                outcome = "PASS"
            elif status in ("blocked", "failed"):
                outcome = "FAIL"
            else:
                outcome = status.upper()

            # Parse duration from note e.g. "Direct: 1 tool call(s) in 49s"
            duration = None
            note = r["duration_note"] or ""
            if "in " in note and note.endswith("s"):
                try:
                    duration = note.split("in ")[-1]
                except Exception:
                    pass

            dispatches.append({
                "id": str(r["ticket_id"]) + r["started_at"],
                "ticket_id": r["ticket_id"],
                "status": outcome,
                "timestamp": r["started_at"],
                "details": f"{duration} - {note}" if duration else note,
            })

        return {"activity": dispatches}

    except Exception as e:
        log.warning("forge/activity DB query failed: %s", e)
        return {"dispatches": []}
