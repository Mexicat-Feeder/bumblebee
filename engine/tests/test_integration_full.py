"""
Phase 8: Full integration test.

Creates a project via the setup pipeline, inserts tickets via decompose,
generates checks, runs the executor with mock Forge that writes real files,
and verifies everything end-to-end.

Then renames the directory and re-runs to prove no hardcoded paths.
"""
import json
import shutil
import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.new_project import NewProjectRequest, create_project
from scripts.decompose import TicketSpec, DecompPlan, commit_plan
from scripts.generate_checks import generate_checks
from engine.state_machine import StateMachine
from engine.event_log import EventLog, init_db
from engine.config import load_config
from engine.executor import Executor
from engine.qa import static_check


# ── Mock Forge ────────────────────────────────────────────────────

MOCK_FILE_CONTENTS = {
    "src/components/base/Card.tsx": (
        'import React from "react";\n'
        'export interface CardProps { children: React.ReactNode; className?: string; }\n'
        'export default function Card({ children, className = "" }: CardProps) {\n'
        '  return <div className={`card ${className}`}>{children}</div>;\n'
        '}\n'
    ),
    "src/components/base/Button.tsx": (
        'import React from "react";\n'
        'export interface ButtonProps { label: string; onClick?: () => void; }\n'
        'export default function Button({ label, onClick }: ButtonProps) {\n'
        '  return <button className="btn" onClick={onClick}>{label}</button>;\n'
        '}\n'
    ),
    "src/shared/api-types.ts": (
        'export interface MediaFile { id: string; name: string; path: string; }\n'
        'export interface ApiRoutes {\n'
        '  "GET /api/library": { response: MediaFile[] };\n'
        '}\n'
    ),
    "src/components/LibraryPanel.tsx": (
        'import React from "react";\n'
        'import Card from "./base/Card";\n'
        'import type { MediaFile } from "../shared/api-types";\n'
        'export default function LibraryPanel() {\n'
        '  return <Card className="library-panel"><h2>Library</h2></Card>;\n'
        '}\n'
    ),
    "src/components/PreviewPanel.tsx": (
        'import React from "react";\n'
        'import Card from "./base/Card";\n'
        'export default function PreviewPanel() {\n'
        '  return <Card className="preview-panel"><h2>Preview</h2></Card>;\n'
        '}\n'
    ),
}


def _make_mock_forge(deliverable_root: Path, ticket_files: dict[str, list[str]]):
    """Mock Forge that writes real files for known tickets."""
    def dispatch(ticket_id, config):
        files = ticket_files.get(ticket_id, [])
        for rel in files:
            content = MOCK_FILE_CONTENTS.get(rel, f"// {ticket_id}\nexport default {{}};\n")
            path = deliverable_root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        # Write evidence
        ev_dir = deliverable_root / "artifacts"
        ev_dir.mkdir(parents=True, exist_ok=True)
        ev = {"ticket": ticket_id, "status": "completed", "files": files}
        (ev_dir / f"{ticket_id}.worker.json").write_text(json.dumps(ev), encoding="utf-8")
        return True, f"wrote {len(files)} files"
    return dispatch


def _make_mock_qa(config):
    """QA does real static checks against disk."""
    def qa(ticket_id, cfg):
        conn = sqlite3.connect(str(cfg.db_path))
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT required_output_files_json FROM ticket_requirements WHERE ticket_id=?",
            (ticket_id,),
        ).fetchone()
        conn.close()
        if not row:
            return True, "no requirements"
        req = {"required_output_files_json": row["required_output_files_json"]}
        r = static_check(ticket_id, req, cfg)
        return r.passed, r.note
    return qa


# ── The tickets ───────────────────────────────────────────────────

def _build_plan():
    return DecompPlan(tickets=[
        TicketSpec(id="G0-CARD", gate=0, description="Base Card component",
                   required_output_files=["src/components/base/Card.tsx"],
                   worker_done_criteria="File exists, exports default"),
        TicketSpec(id="G0-BTN", gate=0, description="Base Button component",
                   required_output_files=["src/components/base/Button.tsx"]),
        TicketSpec(id="G0-API", gate=0, description="Shared API types",
                   required_output_files=["src/shared/api-types.ts"]),
        TicketSpec(id="G1-P", gate=1, description="Library + Preview feature",
                   depends_on=["G0-CARD", "G0-BTN", "G0-API"], is_parent=True),
        TicketSpec(id="G1-LIB", gate=1, description="Library panel using Card + API types",
                   depends_on=["G0-CARD", "G0-API"], parent_id="G1-P",
                   required_output_files=["src/components/LibraryPanel.tsx"],
                   interaction_spec="Panel renders with heading 'Library'"),
        TicketSpec(id="G1-PREV", gate=1, description="Preview panel using Card",
                   depends_on=["G0-CARD"], parent_id="G1-P",
                   required_output_files=["src/components/PreviewPanel.tsx"],
                   interaction_spec="Panel renders with heading 'Preview'"),
    ])


TICKET_FILES = {
    "G0-CARD": ["src/components/base/Card.tsx"],
    "G0-BTN": ["src/components/base/Button.tsx"],
    "G0-API": ["src/shared/api-types.ts"],
    "G1-LIB": ["src/components/LibraryPanel.tsx"],
    "G1-PREV": ["src/components/PreviewPanel.tsx"],
}


# ── Test helper ───────────────────────────────────────────────────

def _run_full_pipeline(base_path: Path, engine_name: str = "eng"):
    """Run the full pipeline under a given base path. Returns (config, conn, results)."""
    engine_root = base_path / engine_name
    engine_root.mkdir(parents=True, exist_ok=True)
    deliverable = base_path / "app-code"

    # Step 1: Create project
    req = NewProjectRequest(
        slug="integ",
        display_name="Integration Test",
        deliverable_root=str(deliverable),
        tech_stack="React + Express",
    )
    proj = create_project(req, engine_root, base_path)
    assert proj.success, proj.errors

    # Step 2: Decompose — first patch cycle_interval to 0 for tests
    cfg_data = json.loads(Path(proj.config_path).read_text(encoding='utf-8'))
    cfg_data['cycle_interval_seconds'] = 0
    Path(proj.config_path).write_text(json.dumps(cfg_data, indent=2), encoding='utf-8')
    config = load_config(proj.config_path)
    conn = sqlite3.connect(str(config.db_path))
    conn.row_factory = sqlite3.Row
    plan = _build_plan()
    dr = commit_plan(plan, conn)
    assert dr.success, dr.errors

    # Step 3: Generate checks
    cr = generate_checks(conn, config.deliverable_root, config.workspace_root, config.checks_dir)
    assert cr.success, cr.errors

    # Step 4: Run executor
    sm = StateMachine()
    el = EventLog(conn)
    mock_forge = _make_mock_forge(config.deliverable_root, TICKET_FILES)
    mock_qa = _make_mock_qa(config)

    ex = Executor(config=config, state_machine=sm, conn=conn, event_log=el,
                  dispatch_fn=mock_forge, qa_fn=mock_qa)
    results = ex.run_loop(max_cycles=30)

    return config, conn, el, results


# ── Phase 8 test ──────────────────────────────────────────────────

def test_full_integration(tmp_path):
    """Full pipeline: create → decompose → checks → executor → all qa_verified."""
    config, conn, el, results = _run_full_pipeline(tmp_path)

    # All tickets qa_verified
    rows = conn.execute("SELECT id, status FROM tickets ORDER BY id").fetchall()
    statuses = {r["id"]: r["status"] for r in rows}
    for tid, st in statuses.items():
        assert st == "qa_verified", f"{tid} ended in '{st}'"

    # Real files on disk
    for rel in MOCK_FILE_CONTENTS:
        p = config.deliverable_root / rel
        assert p.exists(), f"Missing: {rel}"
        assert p.stat().st_size > 0

    # Event log complete
    for tid in statuses:
        events = el.events_for(tid)
        assert len(events) >= 2, f"{tid}: only {len(events)} events"

    # Import chain: LibraryPanel imports Card AND uses shared types
    lib = (config.deliverable_root / "src/components/LibraryPanel.tsx").read_text(encoding="utf-8")
    assert 'import Card' in lib
    assert 'api-types' in lib

    # Completed efficiently
    assert len(results) <= 20, f"Too many cycles: {len(results)}"

    conn.close()


def test_rename_and_rerun(tmp_path):
    """Rename the directory, update config, re-run — proves no hardcoded paths."""
    original = tmp_path / "original"
    original.mkdir()
    config1, conn1, _, _ = _run_full_pipeline(original)
    conn1.close()

    # Copy to a new location
    renamed = tmp_path / "totally-different-name"
    shutil.copytree(original, renamed)

    # Update the config to point to new paths
    config_path = renamed / "projects" / "integ" / "project-config.json"
    data = json.loads(config_path.read_text(encoding="utf-8"))
    # Replace all occurrences of "original" with "totally-different-name"
    text = config_path.read_text(encoding="utf-8")
    text = text.replace(str(original), str(renamed))
    config_path.write_text(text, encoding="utf-8")

    # Also update the projects index
    idx_path = renamed / "projects" / "projects.json"
    if idx_path.exists():
        idx_text = idx_path.read_text(encoding="utf-8")
        idx_text = idx_text.replace(str(original), str(renamed))
        idx_path.write_text(idx_text, encoding="utf-8")

    # Re-load and verify
    config2 = load_config(config_path)
    assert config2.deliverable_root.exists()
    assert config2.db_path.exists()

    # Re-run QA checks against existing files
    conn2 = sqlite3.connect(str(config2.db_path))
    conn2.row_factory = sqlite3.Row
    rows = conn2.execute("SELECT id, status FROM tickets ORDER BY id").fetchall()
    # All should still be qa_verified from the first run
    for r in rows:
        assert r["status"] == "qa_verified", f"{r['id']} is {r['status']} after rename"

    # Static checks still pass on renamed paths
    for tid in TICKET_FILES:
        req_row = conn2.execute(
            "SELECT required_output_files_json FROM ticket_requirements WHERE ticket_id=?",
            (tid,),
        ).fetchone()
        if req_row:
            r = static_check(tid, {"required_output_files_json": req_row["required_output_files_json"]}, config2)
            assert r.passed, f"Static check failed for {tid} after rename: {r.note}"

    conn2.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
