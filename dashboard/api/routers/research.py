from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging
import sqlite3
from pathlib import Path

log = logging.getLogger(__name__)
router = APIRouter(prefix="/research", tags=["research"])

from ..services.config_loader import get_config
from ..services.research_db import list_tickets, get_ticket, get_report, submit_ticket


def _cfg():
    cfg = get_config()
    db = cfg.get("researchDbPath", "")
    root = cfg.get("researchRoot", "")
    if not db:
        raise HTTPException(status_code=503, detail="researchDbPath not configured")
    # Auto-init DB if it doesn't exist yet
    db_path = Path(db)
    if not db_path.exists():
        try:
            db_path.parent.mkdir(parents=True, exist_ok=True)
            if root:
                Path(root, "reports").mkdir(parents=True, exist_ok=True)
            from engine.research_db import init_research_db  # type: ignore
            conn = sqlite3.connect(str(db_path))
            conn.execute("PRAGMA journal_mode=WAL")
            init_research_db(conn)
            conn.close()
            log.info("Auto-initialized research DB at %s", db_path)
        except Exception as exc:
            log.warning("Could not auto-init research DB: %s", exc)
    return db, root


@router.get("/tickets")
def get_tickets():
    db, _ = _cfg()
    return {"tickets": list_tickets(db)}


@router.get("/tickets/{ticket_id}")
def get_ticket_by_id(ticket_id: str):
    db, _ = _cfg()
    ticket = get_ticket(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@router.get("/tickets/{ticket_id}/report")
def get_ticket_report(ticket_id: str):
    db, _ = _cfg()
    ticket = get_ticket(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    content = get_report(ticket.get("report_path"))
    return {
        "ticket_id": ticket_id,
        "report_path": ticket.get("report_path"),
        "content": content,
        "available": content is not None,
    }


class SubmitRequest(BaseModel):
    question: str
    context: Optional[str] = ""
    priority: Optional[int] = 5


@router.post("/submit", status_code=201)
def submit(body: SubmitRequest):
    if not body.question.strip():
        raise HTTPException(status_code=400, detail="question is required")
    db, root = _cfg()
    if not root:
        raise HTTPException(status_code=503, detail="researchRoot not configured")
    result = submit_ticket(db, root, body.question, body.context or "", body.priority or 5)
    return result
