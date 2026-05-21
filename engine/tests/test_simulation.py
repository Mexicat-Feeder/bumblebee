"""
End-to-end simulation: real files on disk, real DB, mock Forge.

Creates a small React project with Gate 0 (base components) and Gate 1
(feature tickets + parent with E2E check). Mock Forge writes actual files.
Executor runs until all tickets reach qa_verified or get stuck.
"""
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from engine.state_machine import StateMachine
from engine.event_log import EventLog, init_db, now_iso
from engine.config import ProjectConfig
from engine.executor import Executor
from engine.qa import static_check


def _setup_project(tmp_path: Path) -> tuple[ProjectConfig, sqlite3.Connection]:
    """Create a real project structure on disk."""
    project_root = tmp_path / "projects" / "sim"
    deliverable_root = tmp_path / "app"
    artifacts_dir = deliverable_root / "artifacts"
    checks_dir = deliverable_root / "checks"

    for d in [project_root, deliverable_root, artifacts_dir, checks_dir,
              deliverable_root / "src" / "components" / "base",
              deliverable_root / "src" / "shared"]:
        d.mkdir(parents=True, exist_ok=True)

    config = ProjectConfig(
        engine_root=tmp_path / "engine",
        project_root=project_root,
        workspace_root=tmp_path,
        deliverable_root=deliverable_root,
        db_path=project_root / "tickets.db",
        artifacts_dir=artifacts_dir,
        checks_dir=checks_dir,
        qa_reports_dir=deliverable_root / "reports",
        forge_agent="forge",
        models={"forge": "sim/mock", "vision": "sim/mock"},
        forge_timeout_seconds=30,
        cycle_interval_seconds=0,
        max_dispatch_attempts=3,
    )

    conn = sqlite3.connect(str(config.db_path))
    conn.row_factory = sqlite3.Row
    init_db(conn)
    return config, conn


def _insert(conn, tid, gate, depends=None, parent=None, files=None, desc=""):
    depends_json = json.dumps(depends or [])
    files_json = json.dumps(files or [])
    conn.execute(
        """INSERT INTO tickets (id, owner, gate, status, depends_on, parent_ticket_id, updated_at)
           VALUES (?,?,?,'todo',?,?,?)""",
        (tid, "sim", gate, depends_json, parent, now_iso()),
    )
    conn.execute(
        """INSERT INTO ticket_requirements 
           (ticket_id, ticket_description, required_output_files_json,
            worker_done_criteria, qa_done_criteria, worker_evidence_json)
           VALUES (?,?,?,?,?,?)""",
        (tid, desc, files_json, f"Files exist for {tid}", f"QA pass for {tid}",
         json.dumps([f"artifacts/{tid}.worker.json"])),
    )
    conn.commit()


# File contents that mock Forge will write
MOCK_FILES = {
    "src/components/base/Card.tsx": '''
import React from "react";
import "./card.css";
export interface CardProps { children: React.ReactNode; className?: string; }
export default function Card({ children, className = "" }: CardProps) {
  return <div className={`card ${className}`}>{children}</div>;
}
''',
    "src/components/base/Button.tsx": '''
import React from "react";
export interface ButtonProps { label: string; onClick?: () => void; variant?: "primary" | "secondary"; }
export default function Button({ label, onClick, variant = "primary" }: ButtonProps) {
  return <button className={`btn btn-${variant}`} onClick={onClick}>{label}</button>;
}
''',
    "src/shared/api-types.ts": '''
export interface MediaFile { id: string; name: string; path: string; type: "image" | "video" | "audio"; }
export interface ApiRoutes {
  "GET /api/library": { response: MediaFile[] };
  "POST /api/generate": { body: { prompt: string; mode: string }; response: { jobId: string } };
}
''',
    "src/components/LibraryPanel.tsx": '''
import React, { useState, useEffect } from "react";
import Card from "./base/Card";
import type { MediaFile } from "../shared/api-types";
export default function LibraryPanel() {
  const [files, setFiles] = useState<MediaFile[]>([]);
  useEffect(() => { fetch("/api/library").then(r => r.json()).then(setFiles); }, []);
  return (
    <Card className="library-panel">
      <h2>Library</h2>
      <ul>{files.map(f => <li key={f.id}>{f.name}</li>)}</ul>
    </Card>
  );
}
''',
    "src/components/PreviewPanel.tsx": '''
import React from "react";
import Card from "./base/Card";
export default function PreviewPanel({ file }: { file?: { name: string; path: string; type: string } }) {
  if (!file) return <Card className="preview-panel"><p>No file selected</p></Card>;
  return (
    <Card className="preview-panel">
      <h2>{file.name}</h2>
      {file.type === "image" && <img src={file.path} alt={file.name} />}
      {file.type === "video" && <video src={file.path} controls />}
    </Card>
  );
}
''',
    "src/server/routes.ts": '''
import { Router, Request, Response } from "express";
import type { MediaFile } from "../shared/api-types";
const router = Router();
const library: MediaFile[] = [];
router.get("/api/library", (_req: Request, res: Response) => { res.json(library); });
router.post("/api/generate", (req: Request, res: Response) => {
  const { prompt, mode } = req.body;
  const jobId = Math.random().toString(36).slice(2);
  res.json({ jobId });
});
export default router;
''',
}


def make_mock_forge(deliverable_root: Path):
    """Create a mock Forge that writes real files."""
    ticket_file_map = {
        "G0-CARD": ["src/components/base/Card.tsx"],
        "G0-BTN": ["src/components/base/Button.tsx"],
        "G0-API": ["src/shared/api-types.ts"],
        "G1-LIB": ["src/components/LibraryPanel.tsx"],
        "G1-PREV": ["src/components/PreviewPanel.tsx"],
        "G1-ROUTE": ["src/server/routes.ts"],
    }

    def mock_dispatch(ticket_id: str, config: ProjectConfig) -> tuple[bool, str]:
        files = ticket_file_map.get(ticket_id, [])
        written = []
        for rel in files:
            content = MOCK_FILES.get(rel, f"// Generated for {ticket_id}\nexport default {{}};")
            path = deliverable_root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content.strip() + "\n", encoding="utf-8")
            written.append(rel)

        # Write worker evidence
        evidence_dir = deliverable_root / "artifacts"
        evidence_dir.mkdir(parents=True, exist_ok=True)
        evidence = {
            "ticket": ticket_id,
            "status": "completed",
            "files_written": written,
        }
        (evidence_dir / f"{ticket_id}.worker.json").write_text(
            json.dumps(evidence, indent=2), encoding="utf-8"
        )
        return True, f"Wrote {len(written)} files for {ticket_id}"

    return mock_dispatch


def make_mock_qa(deliverable_root: Path):
    """QA that does real static checks."""
    def mock_qa(ticket_id: str, config: ProjectConfig) -> tuple[bool, str]:
        # Just check files exist (real static check)
        conn = sqlite3.connect(str(config.db_path))
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT required_output_files_json FROM ticket_requirements WHERE ticket_id=?",
            (ticket_id,),
        ).fetchone()
        conn.close()
        if not row:
            return True, "no requirements"
        req = {"required_output_files_json": row["required_output_files_json"]}
        result = static_check(ticket_id, req, config)
        return result.passed, result.note

    return mock_qa


def test_full_project_simulation(tmp_path):
    """Run a complete 9-ticket project through the executor."""
    config, conn = _setup_project(tmp_path)

    # Gate 0: Base components (no deps)
    _insert(conn, "G0-CARD", 0, files=["src/components/base/Card.tsx"],
            desc="Create base Card component with glass effect")
    _insert(conn, "G0-BTN", 0, files=["src/components/base/Button.tsx"],
            desc="Create base Button with primary/secondary variants")
    _insert(conn, "G0-API", 0, files=["src/shared/api-types.ts"],
            desc="Generate shared API types from architecture")

    # Gate 1: Feature tickets (depend on Gate 0)
    _insert(conn, "G1-P", 1, depends=["G0-CARD", "G0-BTN", "G0-API"], files=[],
            desc="Library + Preview feature (parent)")
    _insert(conn, "G1-LIB", 1, depends=["G0-CARD", "G0-API"],
            parent="G1-P", files=["src/components/LibraryPanel.tsx"],
            desc="Create LibraryPanel using Card and MediaFile type")
    _insert(conn, "G1-PREV", 1, depends=["G0-CARD"],
            parent="G1-P", files=["src/components/PreviewPanel.tsx"],
            desc="Create PreviewPanel using Card")
    _insert(conn, "G1-ROUTE", 1, depends=["G0-API"],
            parent="G1-P", files=["src/server/routes.ts"],
            desc="Create Express routes implementing ApiRoutes contract")

    # Gate 2: Integration (depends on Gate 1 parent)
    _insert(conn, "G2-A", 2, depends=["G1-P"], files=["src/server/routes.ts"],
            desc="Final integration — already exists, just verifying")

    mock_forge = make_mock_forge(config.deliverable_root)
    mock_qa = make_mock_qa(config.deliverable_root)

    sm = StateMachine()
    event_log = EventLog(conn)
    ex = Executor(
        config=config,
        state_machine=sm,
        conn=conn,
        event_log=event_log,
        dispatch_fn=mock_forge,
        qa_fn=mock_qa,
    )

    results = ex.run_loop(max_cycles=30)

    # ── Assertions ────────────────────────────────────────────────

    # 1. All tickets should reach qa_verified
    rows = conn.execute("SELECT id, status FROM tickets ORDER BY id").fetchall()
    statuses = {r["id"]: r["status"] for r in rows}
    print("\n=== Final ticket statuses ===")
    for tid, st in sorted(statuses.items()):
        print(f"  {tid}: {st}")

    for tid, st in statuses.items():
        assert st == "qa_verified", f"{tid} ended in '{st}', expected 'qa_verified'"

    # 2. Real files exist on disk
    for rel_path in MOCK_FILES:
        full = config.deliverable_root / rel_path
        assert full.exists(), f"File not on disk: {rel_path}"
        assert full.stat().st_size > 0, f"File is empty: {rel_path}"

    # 3. Worker evidence artifacts exist
    for tid in ["G0-CARD", "G0-BTN", "G0-API", "G1-LIB", "G1-PREV", "G1-ROUTE"]:
        ev = config.deliverable_root / "artifacts" / f"{tid}.worker.json"
        assert ev.exists(), f"Missing evidence for {tid}"

    # 4. Event log has complete audit trail
    all_events = conn.execute(
        "SELECT ticket_id, from_status, to_status, actor FROM ticket_events ORDER BY id"
    ).fetchall()
    print(f"\n=== Event log ({len(all_events)} events) ===")
    for e in all_events:
        print(f"  {e['ticket_id']}: {e['from_status']} -> {e['to_status']} [{e['actor']}]")

    # Every ticket should have at least 2 events (todo→in_progress, ...→qa_verified)
    for tid in statuses:
        events = event_log.events_for(tid)
        assert len(events) >= 2, f"{tid} has only {len(events)} events"

    # 5. Component library files import correctly
    card = (config.deliverable_root / "src/components/base/Card.tsx").read_text(encoding="utf-8")
    assert "export default" in card
    lib = (config.deliverable_root / "src/components/LibraryPanel.tsx").read_text(encoding="utf-8")
    assert 'import Card from "./base/Card"' in lib
    assert "MediaFile" in lib  # uses shared types

    routes = (config.deliverable_root / "src/server/routes.ts").read_text(encoding="utf-8")
    assert "api-types" in routes  # uses shared API contract

    # 6. Cycles completed efficiently
    total_cycles = len(results)
    print(f"\n=== Completed in {total_cycles} cycles ===")
    assert total_cycles <= 20, f"Took too many cycles: {total_cycles}"

    print("\nFull simulation passed!")


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "-s"])
