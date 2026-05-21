"""
Swarm Engine — Forge Dispatch (Structured Contract)

Forge receives a structured contract, not prose.
The contract includes: task objective, files to write, architecture rules,
constraints, success criteria, interaction spec, and optionally a screenshot
of the current app state.

Clean-slate dispatch is trivial: omit error_context after N attempts.
"""
from __future__ import annotations

import json
import logging
import os
import signal
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import ProjectConfig
from .executor import track_pid
from .vision import get_latest_screenshot_b64
from .postwrite import compute_relative_import

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Dispatch contract
# ---------------------------------------------------------------------------

@dataclass
class DispatchContract:
    """Structured task contract for Forge."""
    task_id: str
    objective: str
    files_to_write: list[str]
    files_to_read: list[str] = field(default_factory=list)
    architecture_rules: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    success_criteria: str = ""
    interaction_spec: str = ""
    app_screenshot_b64: str | None = None
    error_context: str | None = None
    attempt: int = 1
    max_context_tokens: int = 4000

    def to_json(self) -> str:
        d = {
            "task_id": self.task_id,
            "objective": self.objective,
            "files_to_write": self.files_to_write,
            "architecture_rules": self.architecture_rules,
            "constraints": self.constraints,
            "success_criteria": self.success_criteria,
        }
        if self.files_to_read:
            d["files_to_read"] = self.files_to_read
        if self.interaction_spec:
            d["interaction_spec"] = self.interaction_spec
        if self.app_screenshot_b64:
            d["app_screenshot"] = "(base64 image attached)"
        if self.error_context:
            d["previous_error"] = self.error_context
        d["attempt"] = self.attempt
        return json.dumps(d, indent=2)


@dataclass
class DispatchResult:
    """Result of a Forge dispatch."""
    success: bool
    ticket_id: str
    duration_seconds: float = 0.0
    files_written: list[str] = field(default_factory=list)
    error: str = ""
    timed_out: bool = False
    tool_calls: int = 0
    raw_output: str = ""


# ---------------------------------------------------------------------------
# Contract builder
# ---------------------------------------------------------------------------

def build_contract(
    ticket_id: str,
    requirements: dict[str, Any],
    config: ProjectConfig,
    attempt: int = 1,
    app_screenshot_b64: str | None = None,
    last_error: str | None = None,
    architecture_rules: list[str] | None = None,
) -> DispatchContract:
    """Build a dispatch contract from ticket requirements and config."""
    objective = requirements.get("ticket_description", "")
    
    files_to_write = json.loads(requirements.get("required_output_files_json", "[]"))
    files_to_read = json.loads(requirements.get("context_files_json", "[]"))
    constraints = json.loads(requirements.get("constraints_json", "[]"))
    interaction_spec = requirements.get("interaction_spec", "") or ""
    success_criteria = requirements.get("worker_done_criteria", "") or ""

    # Clean-slate: omit error context after 3 attempts
    error_ctx = last_error if attempt < 3 else None

    return DispatchContract(
        task_id=ticket_id,
        objective=objective,
        files_to_write=files_to_write,
        files_to_read=files_to_read,
        architecture_rules=architecture_rules or [],
        constraints=constraints,
        success_criteria=success_criteria,
        interaction_spec=interaction_spec,
        app_screenshot_b64=app_screenshot_b64,
        error_context=error_ctx,
        attempt=attempt,
    )


def format_task_message(contract: DispatchContract) -> str:
    """Format the contract as the task message for the Forge agent."""
    parts = [
        f"## Task Contract\n",
        f"**Task ID:** {contract.task_id}",
        f"**Attempt:** {contract.attempt}",
        f"\n**Objective:**\n{contract.objective}",
        f"\n**Files to write:**",
    ]
    for f in contract.files_to_write:
        parts.append(f"- `{f}`")

    if contract.files_to_read:
        parts.append(f"\n**Files to read first:**")
        for f in contract.files_to_read:
            parts.append(f"- `{f}`")

    if contract.architecture_rules:
        parts.append(f"\n**Architecture rules (MUST follow):**")
        for rule in contract.architecture_rules:
            parts.append(f"- {rule}")

    if contract.constraints:
        parts.append(f"\n**Constraints:**")
        for c in contract.constraints:
            parts.append(f"- {c}")

    if contract.success_criteria:
        parts.append(f"\n**Success criteria:**\n{contract.success_criteria}")

    if contract.interaction_spec:
        parts.append(f"\n**Interaction spec (expected behavior):**\n{contract.interaction_spec}")

    if contract.error_context:
        parts.append(f"\n**Previous attempt error (fix this):**\n```\n{contract.error_context[:2000]}\n```")

    if contract.app_screenshot_b64:
        parts.append(f"\n**Current app screenshot is attached as an image.**")

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Forge dispatch via OpenClaw CLI
# ---------------------------------------------------------------------------

def dispatch_forge(
    contract: DispatchContract,
    config: ProjectConfig,
    timeout_seconds: int | None = None,
) -> DispatchResult:
    """
    Dispatch a task to Forge via `openclaw agent --agent <forge_agent>`.
    
    Blocks until Forge completes or timeout fires.
    On timeout, kills the entire process tree (Windows: taskkill /F /T).
    """
    timeout = timeout_seconds or config.forge_timeout_seconds
    task_message = format_task_message(contract)

    # Find openclaw CLI
    openclaw_cmd = _find_openclaw()
    if not openclaw_cmd:
        return DispatchResult(
            success=False,
            ticket_id=contract.task_id,
            error="openclaw CLI not found",
        )

    cmd = [
        openclaw_cmd, "agent",
        "--agent", config.forge_agent,
        "--message", task_message,
    ]

    started_at = time.time()
    log.info(f"Forge dispatch START ticket={contract.task_id} attempt={contract.attempt}")

    try:
        # Use CREATE_NO_WINDOW on Windows to prevent terminal spam
        kwargs: dict[str, Any] = {
            "capture_output": True,
            "text": True,
            "timeout": timeout,
        }
        if os.name == "nt":
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True,
                                shell=(os.name == "nt"),  # Windows needs shell for .ps1/.cmd wrappers
                                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        track_pid(proc.pid)

        try:
            stdout, stderr = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            # Kill entire process tree on Windows
            if os.name == "nt":
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                    capture_output=True, timeout=10,
                )
            proc.kill()
            proc.communicate()
            
            duration = time.time() - started_at
            log.warning(f"Forge dispatch TIMEOUT ticket={contract.task_id} after {duration:.0f}s")
            return DispatchResult(
                success=False,
                ticket_id=contract.task_id,
                duration_seconds=duration,
                error=f"Forge timed out after {timeout}s",
                timed_out=True,
            )

        duration = time.time() - started_at
        output = (stdout or "") + (stderr or "")

        if proc.returncode == 0:
            # Check if required files were actually written
            deliverable = config.deliverable_root
            written = [f for f in contract.files_to_write if (deliverable / f).exists()]
            missing = [f for f in contract.files_to_write if f not in written]

            if missing:
                log.warning(f"Forge dispatch PARTIAL ticket={contract.task_id} missing={missing}")
                return DispatchResult(
                    success=False,
                    ticket_id=contract.task_id,
                    duration_seconds=duration,
                    files_written=written,
                    error=f"Forge completed but missing files: {missing}",
                    raw_output=output[-2000:],
                )

            log.info(f"Forge dispatch DONE ticket={contract.task_id} in {duration:.0f}s files={len(written)}")
            return DispatchResult(
                success=True,
                ticket_id=contract.task_id,
                duration_seconds=duration,
                files_written=written,
                raw_output=output[-2000:],
            )
        else:
            log.warning(f"Forge dispatch FAILED ticket={contract.task_id} rc={proc.returncode}")
            return DispatchResult(
                success=False,
                ticket_id=contract.task_id,
                duration_seconds=duration,
                error=f"Forge exited with code {proc.returncode}: {output[-1000:]}",
                raw_output=output[-2000:],
            )

    except FileNotFoundError:
        return DispatchResult(
            success=False,
            ticket_id=contract.task_id,
            error=f"Command not found: {cmd[0]}",
        )
    except Exception as e:
        duration = time.time() - started_at
        return DispatchResult(
            success=False,
            ticket_id=contract.task_id,
            duration_seconds=duration,
            error=str(e),
        )


def _find_openclaw() -> str | None:
    """Find the openclaw CLI executable."""
    # Try common locations
    candidates = [
        "openclaw",  # on PATH
        str(Path.home() / "AppData" / "Roaming" / "npm" / "openclaw.cmd"),
        str(Path.home() / "AppData" / "Roaming" / "npm" / "openclaw"),
    ]
    for c in candidates:
        try:
            result = subprocess.run(
                [c, "--version"],
                capture_output=True, text=True, timeout=5,
                shell=(os.name == "nt"),
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            if result.returncode == 0:
                return c
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            continue
    return None
