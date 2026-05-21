"""
Phase 9: Live Forge test.

Dispatches a real ticket to Qwen3.6 via openclaw agent --agent forge.
Forge writes real code. Static checks verify the output.

Run with: python -m pytest bumblebee/engine/tests/test_live_forge.py -v -s
"""
import json
import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from engine.state_machine import StateMachine
from engine.event_log import EventLog, init_db, now_iso
from engine.config import ProjectConfig
from engine.executor import Executor
from engine.qa import static_check
from engine.dispatch import build_contract, format_task_message, DispatchResult


# ── Live dispatch function ────────────────────────────────────────

def _live_forge_dispatch(ticket_id: str, config: ProjectConfig) -> tuple[bool, str]:
    """Dispatch to real Forge via openclaw CLI."""
    conn = sqlite3.connect(str(config.db_path))
    conn.row_factory = sqlite3.Row
    req = conn.execute(
        """SELECT ticket_description, required_output_files_json,
                  worker_done_criteria, interaction_spec, constraints_json,
                  context_files_json
           FROM ticket_requirements WHERE ticket_id=?""",
        (ticket_id,),
    ).fetchone()
    conn.close()

    if not req:
        return False, "no requirements found"

    # Resolve files to absolute paths so Forge writes to the right place
    files_rel = json.loads(req["required_output_files_json"] or "[]")
    files_abs = [str((config.deliverable_root / f).resolve()) for f in files_rel]
    
    requirements_with_abs = dict(req)
    requirements_with_abs["required_output_files_json"] = json.dumps(files_abs)
    
    contract = build_contract(
        ticket_id=ticket_id,
        requirements=requirements_with_abs,
        config=config,
        attempt=1,
        architecture_rules=[
            "Use TypeScript with React 18",
            "All components use default export",
            "Import base components from ./base/ when available",
            "No Node.js built-ins (fs, path, os) in src/",
            "Write files to the EXACT absolute paths listed. Do not change the paths.",
        ],
    )
    task_msg = format_task_message(contract)

    # Flatten task message to single line to avoid shell parsing issues
    # Windows PowerShell breaks on newlines and backticks in --message args
    session_id = f"bumblebee-live-{ticket_id}"
    flat_msg = task_msg.replace('\n', ' ').replace('`', "'").replace('"', "'")
    cmd = ["openclaw", "agent", "--agent", config.raw.get("forge_agent", "forge"),
           "--session-id", session_id, "--message", flat_msg]

    started = time.time()
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=config.forge_timeout_seconds,
            shell=(os.name == "nt"),
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        duration = time.time() - started
        output = (result.stdout or "") + (result.stderr or "")

        if result.returncode != 0:
            return False, f"Forge exited {result.returncode} in {duration:.0f}s: {output[-500:]}"

        # Check files
        files = json.loads(req["required_output_files_json"] or "[]")
        missing = [f for f in files if not (config.deliverable_root / f).exists()]
        if missing:
            return False, f"Forge completed in {duration:.0f}s but missing: {missing}"

        # Write evidence
        ev_dir = config.deliverable_root / "artifacts"
        ev_dir.mkdir(parents=True, exist_ok=True)
        (ev_dir / f"{ticket_id}.worker.json").write_text(json.dumps({
            "ticket": ticket_id, "status": "completed",
            "duration_s": duration,
            "files_written": [f for f in files if (config.deliverable_root / f).exists()],
        }, indent=2), encoding="utf-8")

        return True, f"Forge completed in {duration:.0f}s, {len(files)} files written"

    except subprocess.TimeoutExpired:
        return False, f"Forge timed out after {config.forge_timeout_seconds}s"
    except Exception as e:
        return False, str(e)


def _live_qa(ticket_id: str, config: ProjectConfig) -> tuple[bool, str]:
    """Real static check QA."""
    conn = sqlite3.connect(str(config.db_path))
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT required_output_files_json FROM ticket_requirements WHERE ticket_id=?",
        (ticket_id,),
    ).fetchone()
    conn.close()
    if not row:
        return True, "no requirements"
    r = static_check(ticket_id, {"required_output_files_json": row["required_output_files_json"]}, config)
    return r.passed, r.note


# ── Setup ─────────────────────────────────────────────────────────

@pytest.fixture
def live_project(tmp_path):
    """Create a real project for live Forge testing."""
    deliverable = tmp_path / "live-app"
    deliverable.mkdir()
    (deliverable / "src" / "components" / "base").mkdir(parents=True)
    (deliverable / "src" / "shared").mkdir(parents=True)
    (deliverable / "artifacts").mkdir()

    project_root = tmp_path / "project"
    project_root.mkdir()

    config = ProjectConfig(
        engine_root=tmp_path / "engine",
        project_root=project_root,
        workspace_root=tmp_path,
        deliverable_root=deliverable,
        db_path=project_root / "tickets.db",
        artifacts_dir=deliverable / "artifacts",
        checks_dir=deliverable / "checks",
        qa_reports_dir=deliverable / "reports",
        forge_agent="forge",
        models={"forge": "Qwen3.6-35B-A3B-GGUF", "vision": "Qwen3.6-35B-A3B-GGUF"},
        forge_timeout_seconds=300,
        cycle_interval_seconds=0,
        max_dispatch_attempts=3,
        raw={"forge_agent": "forge"},
    )

    conn = sqlite3.connect(str(config.db_path))
    conn.row_factory = sqlite3.Row
    init_db(conn)

    return config, conn


# ── Tests ─────────────────────────────────────────────────────────

class TestLiveForge:

    def test_single_component_dispatch(self, live_project):
        """Forge writes a real React component."""
        config, conn = live_project

        conn.execute(
            "INSERT INTO tickets (id,owner,gate,status,updated_at) VALUES ('LF-CARD','test',0,'todo',?)",
            (now_iso(),),
        )
        conn.execute(
            """INSERT INTO ticket_requirements 
               (ticket_id, ticket_description, required_output_files_json,
                worker_done_criteria, interaction_spec, worker_evidence_json)
               VALUES (?, ?, ?, ?, ?, ?)""",
            ("LF-CARD",
             "Create a base Card component in React+TypeScript. "
             "It should accept children and an optional className prop. "
             "Use a dark theme with border-radius 12px, background #161B22, "
             "border 1px solid #21262D, and padding 16px.",
             '["src/components/base/Card.tsx"]',
             "File exists, exports default Card component, uses TypeScript",
             "Card renders as a dark rounded container with children inside",
             '["artifacts/LF-CARD.worker.json"]'),
        )
        conn.commit()

        # Dispatch to real Forge
        ok, note = _live_forge_dispatch("LF-CARD", config)
        print(f"\nForge result: ok={ok}, note={note}")

        assert ok, f"Forge failed: {note}"

        # Verify file exists and has real content
        card_path = config.deliverable_root / "src/components/base/Card.tsx"
        assert card_path.exists(), "Card.tsx not written"
        content = card_path.read_text(encoding="utf-8")
        print(f"Card.tsx ({len(content)} chars):\n{content[:500]}")

        assert len(content) > 100, f"Card.tsx too small ({len(content)} chars)"
        assert "export default" in content or "export {" in content, "No export found"

        # QA check
        qa_ok, qa_note = _live_qa("LF-CARD", config)
        assert qa_ok, f"QA failed: {qa_note}"

    def test_full_gate0_with_executor(self, live_project):
        """Run 3 Gate 0 tickets through the executor with real Forge."""
        config, conn = live_project

        tickets = [
            ("G0-CARD", "Create base Card component: dark background #161B22, border-radius 12px, "
             "border 1px solid #21262D, padding 16px. Accept children and className props.",
             '["src/components/base/Card.tsx"]'),
            ("G0-BTN", "Create base Button component: pill shape (border-radius 9999px), "
             "primary variant with background #1F6FEB and white text, "
             "secondary variant with transparent background and border. Accept label, onClick, variant props.",
             '["src/components/base/Button.tsx"]'),
            ("G0-API", "Create shared API types file with TypeScript interfaces: "
             "MediaFile (id, name, path, type), ApiRoutes mapping GET /api/library to MediaFile array.",
             '["src/shared/api-types.ts"]'),
        ]

        for tid, desc, files in tickets:
            conn.execute(
                "INSERT INTO tickets (id,owner,gate,status,updated_at) VALUES (?,?,0,'todo',?)",
                (tid, "test", now_iso()),
            )
            conn.execute(
                """INSERT INTO ticket_requirements 
                   (ticket_id, ticket_description, required_output_files_json,
                    worker_done_criteria, worker_evidence_json)
                   VALUES (?,?,?,?,?)""",
                (tid, desc, files, "File exists and exports correctly",
                 json.dumps([f"artifacts/{tid}.worker.json"])),
            )
        conn.commit()

        sm = StateMachine()
        el = EventLog(conn)
        ex = Executor(config=config, state_machine=sm, conn=conn, event_log=el,
                      dispatch_fn=_live_forge_dispatch, qa_fn=_live_qa)

        results = ex.run_loop(max_cycles=15)

        # Check results
        rows = conn.execute("SELECT id, status FROM tickets ORDER BY id").fetchall()
        print("\n=== Live Gate 0 results ===")
        for r in rows:
            print(f"  {r['id']}: {r['status']}")
            events = el.events_for(r["id"])
            for e in events:
                print(f"    {e.from_status} -> {e.to_status} [{e.actor}]")

        # At least verify files were written (may not all pass QA on first try)
        for tid, _, files_json in tickets:
            for rel in json.loads(files_json):
                p = config.deliverable_root / rel
                if p.exists():
                    content = p.read_text(encoding="utf-8")
                    print(f"\n{rel} ({len(content)} chars)")

        # Count successes
        verified = sum(1 for r in rows if r["status"] == "qa_verified")
        print(f"\n{verified}/{len(tickets)} tickets qa_verified")
        assert verified >= 1, "No tickets reached qa_verified with real Forge"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
