"""
Research Executor Management — start/stop/status the Sift executor.

The Sift executor runs as a background process, polling the research DB
for queued tickets, running web search + LLM, and writing reports.

Endpoints:
  POST /api/research/executor/start
  POST /api/research/executor/stop
  GET  /api/research/executor/status
"""
from __future__ import annotations

import logging
import os
import subprocess
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException

from ..services.config_loader import get_config

log = logging.getLogger(__name__)
router = APIRouter(prefix="/research", tags=["research-executor"])

_BUMBLEBEE_ROOT = Path(__file__).resolve().parent.parent.parent.parent

_executor: dict | None = None
_lock = threading.Lock()


def _resolve_paths() -> tuple[str, str]:
    """Return (db_path, reports_dir) resolved to absolute paths."""
    config = get_config()
    dashboard_root = Path(__file__).resolve().parent.parent.parent

    raw_db = config.get("researchDbPath", "")
    raw_root = config.get("researchRoot", "")

    db_path = Path(raw_db)
    if not db_path.is_absolute():
        db_path = (dashboard_root / db_path).resolve()

    root = Path(raw_root)
    if not root.is_absolute():
        root = (dashboard_root / root).resolve()
    reports_dir = root / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    return str(db_path), str(reports_dir)


def _is_alive(proc: subprocess.Popen | None) -> bool:
    return proc is not None and proc.poll() is None


def _log_path() -> Path:
    config = get_config()
    dashboard_root = Path(__file__).resolve().parent.parent.parent
    raw_root = config.get("researchRoot", "")
    root = Path(raw_root)
    if not root.is_absolute():
        root = (dashboard_root / root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root / "sift-executor.log"


def is_running() -> bool:
    """Check if the Sift executor is currently running."""
    global _executor
    with _lock:
        if _executor and _is_alive(_executor.get("process")):
            return True
        return False


def ensure_running() -> None:
    """Start the executor if not already running. Called on ticket submit."""
    if is_running():
        return
    try:
        _start_executor()
    except Exception as e:
        log.warning("Auto-start Sift executor failed: %s", e)


def _start_executor() -> dict:
    """Internal: start the executor process."""
    global _executor

    db_path, reports_dir = _resolve_paths()
    if not Path(db_path).exists():
        raise HTTPException(status_code=400, detail="Research DB not found")

    script = _BUMBLEBEE_ROOT / "engine" / "research_executor.py"
    if not script.exists():
        raise HTTPException(status_code=500, detail="research_executor.py not found")

    log_file = _log_path()

    with _lock:
        # Check again under lock
        if _executor and _is_alive(_executor.get("process")):
            return {
                "status": "already_running",
                "pid": _executor["process"].pid,
                "started_at": _executor.get("started_at"),
            }

        log_handle = open(log_file, "a", encoding="utf-8")
        proc = subprocess.Popen(
            [sys.executable, str(script),
             "--db-path", db_path,
             "--reports-dir", reports_dir],
            cwd=str(_BUMBLEBEE_ROOT),
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )

        started_at = datetime.now(timezone.utc).isoformat()
        _executor = {
            "process": proc,
            "log_handle": log_handle,
            "log_path": str(log_file),
            "started_at": started_at,
        }

        log.info("Started Sift executor (PID %d)", proc.pid)
        return {
            "status": "started",
            "pid": proc.pid,
            "started_at": started_at,
        }


@router.post("/executor/start")
def start():
    result = _start_executor()
    return result


@router.post("/executor/stop")
def stop():
    global _executor
    with _lock:
        if not _executor or not _is_alive(_executor.get("process")):
            _executor = None
            return {"status": "not_running"}

        proc = _executor["process"]
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
            log.warning("Failed to stop Sift executor: %s", e)

        handle = _executor.get("log_handle")
        if handle:
            try:
                handle.close()
            except Exception:
                pass

        _executor = None
        log.info("Stopped Sift executor")
        return {"status": "stopped"}


@router.get("/executor/status")
def status():
    global _executor
    running = False
    pid = None
    started_at = None

    with _lock:
        if _executor:
            proc = _executor.get("process")
            if _is_alive(proc):
                running = True
                pid = proc.pid
                started_at = _executor.get("started_at")
            else:
                # Process exited — clean up
                handle = _executor.get("log_handle")
                if handle:
                    try:
                        handle.close()
                    except Exception:
                        pass
                _executor = None

    return {
        "running": running,
        "pid": pid,
        "started_at": started_at,
    }


@router.get("/executor/logs")
def logs(lines: int = 50):
    log_file = _log_path()
    if not log_file.exists():
        return {"lines": [], "total_lines": 0}
    try:
        all_lines = log_file.read_text(encoding="utf-8", errors="replace").splitlines()
        tail = all_lines[-lines:] if len(all_lines) > lines else all_lines
        return {"lines": tail, "total_lines": len(all_lines)}
    except Exception as e:
        return {"lines": [f"Error: {e}"], "total_lines": 0}
