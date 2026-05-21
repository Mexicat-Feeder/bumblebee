"""
Swarm Engine — Check Script Generator

Generates worker check scripts (file existence + size) for each ticket.
All paths resolve from config — no hardcoded project names.

Designed as importable functions for both CLI and future dashboard use.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_ENGINE_ROOT = Path(__file__).resolve().parents[1] / "engine"
sys.path.insert(0, str(_ENGINE_ROOT.parent))

from engine.config import load_config


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class CheckGenResult:
    """Result of generating check scripts."""
    success: bool
    scripts_generated: int = 0
    scripts_skipped: int = 0
    errors: list[str] = field(default_factory=list)
    generated_paths: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "scripts_generated": self.scripts_generated,
            "scripts_skipped": self.scripts_skipped,
            "errors": self.errors,
            "generated_paths": self.generated_paths,
        }


# ---------------------------------------------------------------------------
# Check script template
# ---------------------------------------------------------------------------

_WORKER_CHECK_TEMPLATE = '''#!/usr/bin/env python3
"""Worker check for {ticket_id}. Auto-generated — do not edit."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

TICKET_ID = {ticket_id_repr}
REQUIRED_FILES = {required_files_repr}
EVIDENCE_PATH = Path({evidence_path_repr})

_MIN_SIZES = {{
    ".tsx": 150, ".jsx": 150, ".ts": 150, ".js": 150,
    ".css": 50, ".json": 20,
}}

def main() -> int:
    errors, passed = [], []
    for abs_path_str in REQUIRED_FILES:
        p = Path(abs_path_str)
        if not p.exists():
            errors.append(f"FAIL: {{p.name}} missing ({{abs_path_str}})")
        elif p.stat().st_size == 0:
            errors.append(f"FAIL: {{p.name}} empty")
        else:
            size = p.stat().st_size
            min_size = 5 if p.name.endswith(".d.ts") else _MIN_SIZES.get(p.suffix.lower(), 0)
            if size < min_size:
                errors.append(f"FAIL: {{p.name}} stub ({{size}}b < {{min_size}}b)")
            else:
                passed.append(abs_path_str)
    if errors:
        for e in errors:
            print(e)
        return 1
    EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE_PATH.write_text(json.dumps({{
        "ticket": TICKET_ID, "status": "completed",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "files_checked": [Path(p).name for p in passed],
    }}, indent=2), encoding="utf-8")
    print(f"All {{len(passed)}} file(s) verified.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
'''


# ---------------------------------------------------------------------------
# Core function
# ---------------------------------------------------------------------------

def generate_checks(
    conn: sqlite3.Connection,
    deliverable_root: Path,
    workspace_root: Path,
    checks_dir: Path | None = None,
) -> CheckGenResult:
    """
    Generate worker check scripts for all child tickets.
    
    Returns structured result — dashboard can display this.
    """
    result = CheckGenResult(success=False)

    worker_checks_dir = (checks_dir or deliverable_root / "checks") / "worker"
    worker_checks_dir.mkdir(parents=True, exist_ok=True)

    rows = conn.execute("""
        SELECT t.id, r.required_output_files_json, r.worker_evidence_json,
               r.worker_done_criteria
        FROM tickets t
        JOIN ticket_requirements r ON r.ticket_id = t.id
        WHERE t.parent_ticket_id IS NOT NULL OR t.id NOT IN (
            SELECT DISTINCT parent_ticket_id FROM tickets
            WHERE parent_ticket_id IS NOT NULL
        )
        ORDER BY t.id
    """).fetchall()

    for row in rows:
        ticket_id = row["id"]
        files_json = row["required_output_files_json"] or "[]"
        evidence_json = row["worker_evidence_json"] or "[]"

        try:
            required_files = json.loads(files_json)
        except json.JSONDecodeError:
            required_files = []

        if not required_files:
            result.scripts_skipped += 1
            continue

        # Resolve to absolute paths
        abs_files = [str((deliverable_root / f).resolve()) for f in required_files]

        # Evidence path
        try:
            evidence_items = json.loads(evidence_json)
        except json.JSONDecodeError:
            evidence_items = []
        if not evidence_items:
            result.scripts_skipped += 1
            continue
        evidence_abs = str((workspace_root / evidence_items[0]).resolve()) if evidence_items else ""
        if not evidence_abs:
            # Fallback: generate evidence path
            evidence_abs = str((deliverable_root / "artifacts" / f"{ticket_id}.worker.json").resolve())

        script_content = _WORKER_CHECK_TEMPLATE.format(
            ticket_id=ticket_id,
            ticket_id_repr=repr(ticket_id),
            required_files_repr=json.dumps(abs_files, indent=4),
            evidence_path_repr=repr(evidence_abs),
        )

        script_path = worker_checks_dir / f"{ticket_id}.py"
        script_path.write_text(script_content, encoding="utf-8")
        result.scripts_generated += 1
        result.generated_paths.append(str(script_path))

    result.success = True
    return result


# ---------------------------------------------------------------------------
# CLI wrapper
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Generate worker check scripts")
    parser.add_argument("--config", required=True, help="Path to project-config.json")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    config = load_config(args.config)
    conn = sqlite3.connect(str(config.db_path))
    conn.row_factory = sqlite3.Row

    result = generate_checks(
        conn=conn,
        deliverable_root=config.deliverable_root,
        workspace_root=config.workspace_root,
        checks_dir=config.checks_dir,
    )
    conn.close()

    print(json.dumps(result.to_dict(), indent=2))
    return 0 if result.success else 1


if __name__ == "__main__":
    sys.exit(main())
