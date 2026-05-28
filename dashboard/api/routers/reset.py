"""
Demo Reset — clear all tickets, research, and project state back to intake-ready.

POST /api/reset
"""
from __future__ import annotations

import logging
import os
import shutil
import sqlite3
from pathlib import Path

from fastapi import APIRouter, HTTPException

from ..services.config_loader import get_config, save_config
from ..services.registry import list_projects, update_project

log = logging.getLogger(__name__)
router = APIRouter(tags=["reset"])

_BUMBLEBEE_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def _stop_executor(slug: str) -> None:
    """Best-effort stop of a running executor."""
    try:
        from .executor import stop_executor
        stop_executor(slug)
    except Exception:
        pass


def _stop_sift() -> None:
    """Best-effort stop of the Sift executor."""
    try:
        from .research_executor import stop
        stop()
    except Exception:
        pass


def _clear_tickets_db(db_path: str) -> int:
    """Delete all tickets and requirements. Returns count deleted."""
    if not db_path or not Path(db_path).exists():
        return 0
    try:
        conn = sqlite3.connect(db_path, timeout=10)
        count = conn.execute("SELECT count(*) FROM tickets").fetchone()[0]
        conn.execute("DELETE FROM ticket_requirements")
        conn.execute("DELETE FROM tickets")
        conn.commit()
        conn.close()
        return count
    except Exception as e:
        log.warning("Failed to clear tickets in %s: %s", db_path, e)
        return 0


def _clear_research_db(db_path: str) -> int:
    """Delete all research tickets and queue entries. Returns count deleted."""
    if not db_path or not Path(db_path).exists():
        return 0
    try:
        conn = sqlite3.connect(db_path, timeout=10)
        count = conn.execute("SELECT count(*) FROM tickets WHERE id LIKE 'RSH-%'").fetchone()[0]
        conn.execute("DELETE FROM research_queue")
        conn.execute("DELETE FROM ticket_requirements WHERE ticket_id LIKE 'RSH-%'")
        conn.execute("DELETE FROM tickets WHERE id LIKE 'RSH-%'")
        conn.commit()
        conn.close()
        return count
    except Exception as e:
        log.warning("Failed to clear research DB at %s: %s", db_path, e)
        return 0


def _clear_reports(research_root: str) -> int:
    """Delete all report files."""
    if not research_root:
        return 0
    reports_dir = Path(research_root) / "reports"
    if not reports_dir.exists():
        return 0
    count = 0
    for f in reports_dir.glob("RSH-*.report.md"):
        try:
            f.unlink()
            count += 1
        except Exception:
            pass
    return count


def _clear_decomp_cache(slug: str) -> None:
    """Remove cached decomposition plan."""
    dashboard_root = Path(__file__).resolve().parent.parent.parent
    for base in [dashboard_root.parent / "demos" / slug, _BUMBLEBEE_ROOT / "projects" / slug]:
        plan = base / "decomp-plan.json"
        if plan.exists():
            try:
                plan.unlink()
            except Exception:
                pass


def _clear_artifacts(slug: str) -> int:
    """Clear build artifacts directory."""
    dashboard_root = Path(__file__).resolve().parent.parent.parent
    count = 0
    for base in [dashboard_root.parent / "demos" / slug, _BUMBLEBEE_ROOT / "projects" / slug]:
        arts = base / "artifacts"
        if arts.exists():
            for f in arts.iterdir():
                try:
                    if f.is_file():
                        f.unlink()
                        count += 1
                except Exception:
                    pass
        # Also clear output dir
        output = base / "output"
        if output.exists():
            try:
                shutil.rmtree(output)
                output.mkdir(parents=True, exist_ok=True)
                count += 1
            except Exception:
                pass
    return count


@router.post("/reset")
def reset_demo():
    """Reset all demo state back to beginning."""
    config = get_config()
    dashboard_root = Path(__file__).resolve().parent.parent.parent

    results = {
        "tickets_cleared": 0,
        "research_cleared": 0,
        "reports_cleared": 0,
        "artifacts_cleared": 0,
        "projects_reset": [],
    }

    # Stop all executors
    projects = list_projects()
    for p in projects:
        slug = p.get("slug", "")
        if slug:
            _stop_executor(slug)
    _stop_sift()

    # Clear project tickets
    db_paths = config.get("ticketDbPaths", {})
    for slug, db_path in db_paths.items():
        # Resolve relative paths
        dp = Path(db_path)
        if not dp.is_absolute():
            dp = (dashboard_root / dp).resolve()
        results["tickets_cleared"] += _clear_tickets_db(str(dp))
        _clear_decomp_cache(slug)
        results["artifacts_cleared"] += _clear_artifacts(slug)

    # Clear research
    raw_db = config.get("researchDbPath", "")
    raw_root = config.get("researchRoot", "")
    db_path = Path(raw_db)
    if not db_path.is_absolute():
        db_path = (dashboard_root / db_path).resolve()
    root_path = Path(raw_root)
    if not root_path.is_absolute():
        root_path = (dashboard_root / root_path).resolve()

    results["research_cleared"] = _clear_research_db(str(db_path))
    results["reports_cleared"] = _clear_reports(str(root_path))

    # Reset project statuses back to qa_complete (ready for decompose)
    for p in projects:
        slug = p.get("slug", "")
        if not slug:
            continue
        update_project(slug, {
            "status": "qa_complete",
            "checklist": {
                **p.get("checklist", {}),
                "approved": False,
                "scaffolded": False,
                "running": False,
            },
        })
        results["projects_reset"].append(slug)

    # Clear executor log files
    for slug in db_paths:
        for base in [dashboard_root.parent / "demos" / slug, _BUMBLEBEE_ROOT / "projects" / slug]:
            log_file = base / "executor.log"
            if log_file.exists():
                try:
                    log_file.write_text("", encoding="utf-8")
                except Exception:
                    pass

    log.info("Demo reset complete: %s", results)
    return {"ok": True, **results}
