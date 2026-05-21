import json
import logging
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from ..services.config_loader import get_config
from ..services.db_watcher import DbWatcher

log = logging.getLogger(__name__)
router = APIRouter(tags=["tickets"])
_watchers: dict[str, DbWatcher] = {}


def _get_watcher(slug: str) -> DbWatcher | None:
    if slug in _watchers:
        return _watchers[slug]
    config = get_config()
    db_paths = config.get("ticketDbPaths", {})
    if slug not in db_paths:
        return None
    _watchers[slug] = DbWatcher(db_paths[slug])
    return _watchers[slug]


@router.get("/tickets/{slug}")
async def get_tickets(slug: str):
    watcher = _get_watcher(slug)
    if not watcher:
        return {"error": f"Unknown project: {slug}", "tickets": []}
    return {"tickets": watcher.get_all_tickets()}


@router.get("/tickets/{slug}/{ticket_id}/detail")
async def get_ticket_detail(slug: str, ticket_id: str):
    watcher = _get_watcher(slug)
    if not watcher:
        return {"error": f"Unknown project: {slug}"}
    import sqlite3
    config = get_config()
    db_path = config.get("ticketDbPaths", {}).get(slug)
    if not db_path:
        return {"error": "No DB path"}
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """
            SELECT t.*, r.ticket_description, r.worker_done_criteria, r.qa_done_criteria,
                   r.context_files_json, r.required_output_files_json, r.qa_cmd_json
            FROM tickets t
            LEFT JOIN ticket_requirements r ON r.ticket_id = t.id
            WHERE t.id = ?
            """,
            (ticket_id,),
        ).fetchone()
        conn.close()
        if not row:
            return {"error": "Ticket not found"}
        return dict(row)
    except Exception as e:
        log.warning("detail fetch error: %s", e)
        return {"error": str(e)}


@router.get("/tickets/{slug}/stream")
async def ticket_stream(slug: str, request: Request):
    watcher = _get_watcher(slug)
    if not watcher:
        return {"error": f"Unknown project: {slug}"}
    async def generate():
        async for event in watcher.watch():
            if await request.is_disconnected():
                break
            yield f"data: {json.dumps(event)}\n\n"
    return StreamingResponse(generate(), media_type="text/event-stream")
