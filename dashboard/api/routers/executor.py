"""
Executor Management — start/stop/status the coding engine per project.

Endpoints:
  POST /api/projects/{slug}/executor/start    — spawn executor subprocess
  POST /api/projects/{slug}/executor/stop     — kill executor subprocess
  GET  /api/projects/{slug}/executor/status    — running/stopped + last info
  GET  /api/projects/{slug}/executor/logs      — recent log output
"""
from __future__ import annotations

import json
import logging
import os
import signal
import sqlite3
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException

from ..services.config_loader import get_config, save_config
from ..services.registry import get_project, update_project

log = logging.getLogger(__name__)
router = APIRouter(prefix="/projects", tags=["executor"])

_BUMBLEBEE_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# In-memory process tracking
_executors: dict[str, dict] = {}  # slug → {"process": Popen, "log_path": str, "started_at": str}
_lock = threading.Lock()


def _projects_dir(slug: str) -> Path:
    config = get_config()
    ws = config.get("workspaceRoot", "")
    if ws:
        return Path(ws) / "bumblebee" / "projects" / slug
    return _BUMBLEBEE_ROOT / "projects" / slug


def _log_path(slug: str) -> Path:
    d = _projects_dir(slug)
    d.mkdir(parents=True, exist_ok=True)
    return d / "executor.log"


def _pid_path(slug: str) -> Path:
    return _projects_dir(slug) / "executor.pid"


def _write_run_executor(slug: str, project_dir: Path) -> Path:
    """Generate a run_executor.py for this project if one doesn't exist."""
    script = project_dir / "run_executor.py"
    if script.exists():
        return script

    # Generate a minimal executor script
    bumblebee_root = str(_BUMBLEBEE_ROOT.parent).replace("\\", "\\\\")
    content = f'''"""Run the bumblebee executor for {slug}."""
import sys, os
sys.path.insert(0, r'{bumblebee_root}')

from bumblebee.engine.executor import Executor
from bumblebee.engine.state_machine import StateMachine
from bumblebee.engine.event_log import EventLog
from bumblebee.engine.config import load_config
import sqlite3, logging, time, json

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger(__name__)

config = load_config(os.path.join(os.path.dirname(__file__), 'project-config.json'))
conn = sqlite3.connect(str(config.db_path))
conn.row_factory = sqlite3.Row
sm = StateMachine()
ev = EventLog(conn)
ex = Executor(config, sm, conn, ev)

log.info("Starting executor for {slug}...")
start = time.time()
results = ex.run_loop(max_cycles=200)
elapsed = time.time() - start

log.info("=== EXECUTOR COMPLETE ===")
log.info(f"Cycles: {{len(results)}}, Time: {{elapsed:.1f}}s")
total_dispatched = sum(r.tickets_dispatched for r in results)
total_verified = sum(r.tickets_verified for r in results)
log.info(f"Dispatched: {{total_dispatched}}, Verified: {{total_verified}}")

for row in conn.execute("SELECT status, count(*) as n FROM tickets GROUP BY status ORDER BY status"):
    log.info(f"  {{row[\\'status\\']}}: {{row[\\'n\\']}}")
'''
    script.write_text(content, encoding="utf-8")
    return script


def _is_process_alive(pid: int) -> bool:
    """Check if a process with the given PID is still running."""
    try:
        if os.name == "nt":
            result = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
                capture_output=True, text=True, timeout=5,
            )
            return str(pid) in result.stdout
        else:
            os.kill(pid, 0)
            return True
    except (ProcessLookupError, OSError, subprocess.TimeoutExpired):
        return False


def _get_ticket_stats(slug: str) -> dict:
    """Get ticket status counts from the project DB."""
    config = get_config()
    db_paths = config.get("ticketDbPaths", {})
    db_path = db_paths.get(slug)
    if not db_path or not Path(db_path).exists():
        # Try the project dir
        project_dir = _projects_dir(slug)
        db_path = str(project_dir / "tickets.db")
        if not Path(db_path).exists():
            return {}
    try:
        conn = sqlite3.connect(db_path, timeout=2)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT status, COUNT(*) as n FROM tickets GROUP BY status"
        ).fetchall()
        conn.close()
        return {row["status"]: row["n"] for row in rows}
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/{slug}/executor/start")
def start_executor(slug: str):
    """Spawn the executor as a background subprocess."""
    project = get_project(slug)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    with _lock:
        # Check if already running
        existing = _executors.get(slug)
        if existing:
            proc = existing.get("process")
            if proc and proc.poll() is None:
                return {
                    "status": "already_running",
                    "pid": proc.pid,
                    "started_at": existing.get("started_at"),
                }

        project_dir = _projects_dir(slug)
        if not (project_dir / "project-config.json").exists():
            raise HTTPException(
                status_code=400,
                detail="Project not scaffolded. Run decomposition first.",
            )

        # Ensure run_executor.py exists
        script = _write_run_executor(slug, project_dir)
        log_file = _log_path(slug)

        # Spawn subprocess
        try:
            log_handle = open(log_file, "w", encoding="utf-8")
            proc = subprocess.Popen(
                [sys.executable, str(script)],
                cwd=str(project_dir),
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to start executor: {e}")

        started_at = datetime.now(timezone.utc).isoformat()
        _executors[slug] = {
            "process": proc,
            "log_path": str(log_file),
            "log_handle": log_handle,
            "started_at": started_at,
        }

        # Save PID for reattach
        _pid_path(slug).write_text(str(proc.pid), encoding="utf-8")

        # Update project status
        checklist = {**project.get("checklist", {}), "running": True}
        update_project(slug, {"status": "running", "checklist": checklist})

        log.info("Started executor for '%s' (PID %d)", slug, proc.pid)

        return {
            "status": "started",
            "pid": proc.pid,
            "started_at": started_at,
            "log_path": str(log_file),
        }


@router.post("/{slug}/executor/stop")
def stop_executor(slug: str):
    """Stop the executor subprocess."""
    project = get_project(slug)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    with _lock:
        existing = _executors.get(slug)
        if not existing:
            # Try PID file
            pid_file = _pid_path(slug)
            if pid_file.exists():
                try:
                    pid = int(pid_file.read_text().strip())
                    if _is_process_alive(pid):
                        if os.name == "nt":
                            subprocess.run(
                                ["taskkill", "/F", "/T", "/PID", str(pid)],
                                capture_output=True, timeout=10,
                            )
                        else:
                            os.kill(pid, signal.SIGTERM)
                        pid_file.unlink(missing_ok=True)
                        update_project(slug, {"status": "approved"})
                        return {"status": "stopped", "pid": pid}
                except Exception:
                    pass
            return {"status": "not_running"}

        proc = existing.get("process")
        if proc and proc.poll() is None:
            try:
                if os.name == "nt":
                    subprocess.run(
                        ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                        capture_output=True, timeout=10,
                    )
                else:
                    proc.terminate()
                    proc.wait(timeout=10)
            except Exception as e:
                log.warning("Failed to stop executor for '%s': %s", slug, e)

        # Close log handle
        handle = existing.get("log_handle")
        if handle:
            try:
                handle.close()
            except Exception:
                pass

        del _executors[slug]
        _pid_path(slug).unlink(missing_ok=True)

        # Update project status back to approved
        checklist = {**project.get("checklist", {}), "running": False}
        update_project(slug, {"status": "approved", "checklist": checklist})

        log.info("Stopped executor for '%s'", slug)
        return {"status": "stopped"}


@router.get("/{slug}/executor/status")
def executor_status(slug: str):
    """Get executor status for a project."""
    project = get_project(slug)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    running = False
    pid = None
    started_at = None

    with _lock:
        existing = _executors.get(slug)
        if existing:
            proc = existing.get("process")
            if proc and proc.poll() is None:
                running = True
                pid = proc.pid
                started_at = existing.get("started_at")
            else:
                # Process exited — clean up
                handle = existing.get("log_handle")
                if handle:
                    try:
                        handle.close()
                    except Exception:
                        pass
                del _executors[slug]
                _pid_path(slug).unlink(missing_ok=True)

    # Try PID file if not tracked in memory
    if not running:
        pid_file = _pid_path(slug)
        if pid_file.exists():
            try:
                file_pid = int(pid_file.read_text().strip())
                if _is_process_alive(file_pid):
                    running = True
                    pid = file_pid
                else:
                    pid_file.unlink(missing_ok=True)
            except Exception:
                pass

    ticket_stats = _get_ticket_stats(slug)

    return {
        "running": running,
        "pid": pid,
        "started_at": started_at,
        "ticket_stats": ticket_stats,
    }


@router.get("/{slug}/executor/logs")
def executor_logs(slug: str, lines: int = 50):
    """Get recent log output from the executor."""
    log_file = _log_path(slug)
    if not log_file.exists():
        return {"lines": [], "total_lines": 0}

    try:
        all_lines = log_file.read_text(encoding="utf-8", errors="replace").splitlines()
        tail = all_lines[-lines:] if len(all_lines) > lines else all_lines
        return {
            "lines": tail,
            "total_lines": len(all_lines),
        }
    except Exception as e:
        return {"lines": [f"Error reading log: {e}"], "total_lines": 0}
