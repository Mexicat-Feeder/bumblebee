"""
Swarm Engine — Screenshot & App Lifecycle

Handles: kill port → launch app → take screenshot → kill app.
Process group management for clean teardown on Windows.
"""
from __future__ import annotations

import logging
import os
import signal
import socket
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)


@dataclass
class AppProcess:
    """A launched app process with its PID."""
    proc: subprocess.Popen
    pid: int
    port: int


def kill_port(port: int) -> None:
    """Kill any process listening on the given port."""
    if os.name == "nt":
        # Find PID on port
        try:
            result = subprocess.run(
                ["netstat", "-ano"],
                capture_output=True, text=True, timeout=10,
                shell=True, creationflags=subprocess.CREATE_NO_WINDOW,
            )
            for line in result.stdout.split("\n"):
                if f":{port}" in line and "LISTENING" in line:
                    parts = line.strip().split()
                    if parts:
                        pid = parts[-1]
                        try:
                            subprocess.run(
                                ["taskkill", "/F", "/T", "/PID", pid],
                                capture_output=True, timeout=10,
                                creationflags=subprocess.CREATE_NO_WINDOW,
                            )
                            log.info(f"Killed process {pid} on port {port}")
                        except (subprocess.TimeoutExpired, OSError):
                            pass
                        break
        except (subprocess.TimeoutExpired, OSError):
            pass
    else:
        try:
            result = subprocess.run(
                ["lsof", "-ti", f":{port}"],
                capture_output=True, text=True, timeout=10,
            )
            for pid in result.stdout.strip().split("\n"):
                if pid.strip():
                    try:
                        os.kill(int(pid.strip()), signal.SIGTERM)
                    except (ProcessLookupError, ValueError):
                        pass
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass


def is_port_free(port: int) -> bool:
    """Check if a port is free."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False


def ensure_node_modules(cwd: str) -> bool:
    """Run npm install if node_modules is missing. Returns True if ready."""
    cwd_path = Path(cwd)
    if (cwd_path / "node_modules").exists():
        return True
    if not (cwd_path / "package.json").exists():
        return True  # no package.json, nothing to install
    log.info(f"Running npm install in {cwd}")
    try:
        result = subprocess.run(
            ["npm", "install"],
            cwd=cwd, capture_output=True, text=True, timeout=120,
            shell=(os.name == "nt"),
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, OSError) as e:
        log.error(f"npm install failed: {e}")
        return False


def launch_app(
    cmd: list[str],
    cwd: str,
    port: int,
    startup_wait: int = 12,
) -> AppProcess | None:
    """Launch an app process and wait for it to be ready."""
    # Ensure dependencies are installed
    ensure_node_modules(cwd)
    try:
        kwargs: dict[str, Any] = {
            "cwd": cwd,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE,
        }
        if os.name == "nt":
            # Use shell=True on Windows so npm/npx .ps1/.cmd wrappers resolve
            kwargs["shell"] = True
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP

        proc = subprocess.Popen(cmd, **kwargs)
        log.info(f"Launched app (PID {proc.pid}) on port {port}")

        # Wait for port to become active
        for _ in range(startup_wait * 2):
            if not is_port_free(port):
                return AppProcess(proc=proc, pid=proc.pid, port=port)
            time.sleep(0.5)

        # Timeout — port never opened
        log.warning(f"App didn't start on port {port} within {startup_wait}s")
        kill_app(AppProcess(proc=proc, pid=proc.pid, port=port))
        return None

    except (FileNotFoundError, OSError) as e:
        log.error(f"Failed to launch app: {e}")
        return None


def kill_app(app: AppProcess) -> None:
    """Kill the app and its entire process tree."""
    try:
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(app.pid)],
                capture_output=True, timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        else:
            os.kill(app.pid, signal.SIGTERM)
            app.proc.wait(timeout=5)
    except (ProcessLookupError, OSError, subprocess.TimeoutExpired):
        try:
            app.proc.kill()
        except (ProcessLookupError, OSError):
            pass
    log.info(f"Killed app (PID {app.pid})")


def take_screenshot(
    url: str,
    output_dir: str,
    filename: str = "screenshot.png",
    timeout: int = 30,
) -> str | None:
    """Take a screenshot of the running app. Returns path or None."""
    output_path = Path(output_dir) / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Try playwright first
    try:
        script = f"""
import sys
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={{"width": 1280, "height": 720}})
    page.goto("{url}", wait_until="networkidle", timeout=20000)
    page.screenshot(path=r"{output_path}")
    browser.close()
"""
        result = subprocess.run(
            ["python", "-c", script],
            capture_output=True, text=True, timeout=timeout,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        if result.returncode == 0 and output_path.exists():
            log.info(f"Screenshot captured: {output_path}")
            return str(output_path)
        else:
            log.warning(f"Playwright screenshot failed: {result.stderr[:200]}")
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        log.warning(f"Playwright not available: {e}")

    # Fallback: just note that we couldn't take a screenshot
    log.warning("No screenshot method available")
    return None
