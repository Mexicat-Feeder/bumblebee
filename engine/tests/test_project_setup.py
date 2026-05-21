"""Tests for the project setup pipeline (Phase 7)."""
import json
import sqlite3
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.new_project import NewProjectRequest, create_project, NewProjectResult
from scripts.decompose import TicketSpec, DecompPlan, commit_plan, generate_decomp_plan
from scripts.generate_checks import generate_checks
from engine.event_log import init_db


# ── New project tests ─────────────────────────────────────────────

class TestNewProject:

    def test_creates_valid_structure(self, tmp_path):
        engine_root = tmp_path / "engine"
        engine_root.mkdir()
        req = NewProjectRequest(
            slug="test-proj",
            display_name="Test Project",
            deliverable_root=str(tmp_path / "app"),
            tech_stack="React + Express",
        )
        result = create_project(req, engine_root, tmp_path)
        assert result.success, result.errors
        assert Path(result.project_root).exists()
        assert Path(result.config_path).exists()
        assert Path(result.db_path).exists()
        assert (tmp_path / "app" / "src").exists()
        assert (tmp_path / "app" / "artifacts").exists()
        assert (tmp_path / "app" / "checks" / "worker").exists()

    def test_config_has_no_hardcoded_paths(self, tmp_path):
        engine_root = tmp_path / "engine"
        engine_root.mkdir()
        req = NewProjectRequest(
            slug="myapp",
            display_name="My App",
            deliverable_root=str(tmp_path / "myapp-code"),
            tech_stack="React",
        )
        result = create_project(req, engine_root, tmp_path)
        config = json.loads(Path(result.config_path).read_text(encoding="utf-8"))
        # Config should reference the actual paths, not hardcoded ones
        assert "myapp-code" in config["deliverable_root"]
        assert config["models"]["forge"] == ""  # not hardcoded

    def test_projects_index_updated(self, tmp_path):
        engine_root = tmp_path / "engine"
        engine_root.mkdir()
        req = NewProjectRequest(slug="p1", display_name="P1",
                                deliverable_root=str(tmp_path / "p1"), tech_stack="x")
        create_project(req, engine_root, tmp_path)
        
        index_path = tmp_path / "projects" / "projects.json"
        assert index_path.exists()
        index = json.loads(index_path.read_text(encoding="utf-8"))
        assert len(index["projects"]) == 1
        assert index["projects"][0]["slug"] == "p1"
        assert index["projects"][0]["active"] is True

    def test_duplicate_slug_rejected(self, tmp_path):
        engine_root = tmp_path / "engine"
        engine_root.mkdir()
        req = NewProjectRequest(slug="dup", display_name="Dup",
                                deliverable_root=str(tmp_path / "dup"), tech_stack="x")
        create_project(req, engine_root, tmp_path)
        result2 = create_project(req, engine_root, tmp_path)
        assert not result2.success
        assert "already exists" in result2.errors[0]

    def test_missing_slug_rejected(self, tmp_path):
        engine_root = tmp_path / "engine"
        engine_root.mkdir()
        req = NewProjectRequest(slug="", display_name="X",
                                deliverable_root=str(tmp_path / "x"), tech_stack="x")
        result = create_project(req, engine_root, tmp_path)
        assert not result.success

    def test_visual_ref_copied(self, tmp_path):
        engine_root = tmp_path / "engine"
        engine_root.mkdir()
        vis = tmp_path / "ref.png"
        vis.write_bytes(b'\x89PNG fake image data')
        req = NewProjectRequest(slug="vis", display_name="Vis",
                                deliverable_root=str(tmp_path / "vis"),
                                tech_stack="x", visual_ref_path=str(vis))
        result = create_project(req, engine_root, tmp_path)
        assert result.success
        copied = Path(result.project_root) / "visual-refs" / "ref.png"
        assert copied.exists()

    def test_result_is_serializable(self, tmp_path):
        """Result.to_dict() produces valid JSON — dashboard can consume it."""
        engine_root = tmp_path / "engine"
        engine_root.mkdir()
        req = NewProjectRequest(slug="ser", display_name="Ser",
                                deliverable_root=str(tmp_path / "ser"), tech_stack="x")
        result = create_project(req, engine_root, tmp_path)
        d = result.to_dict()
        json_str = json.dumps(d)  # must not raise
        parsed = json.loads(json_str)
        assert parsed["success"] is True


# ── Decomposition tests ───────────────────────────────────────────

class TestDecomposition:

    def _make_db(self, tmp_path):
        db_path = tmp_path / "tickets.db"
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        init_db(conn)
        return conn

    def test_commit_plan_creates_tickets(self, tmp_path):
        conn = self._make_db(tmp_path)
        plan = DecompPlan(tickets=[
            TicketSpec(id="G0-A", gate=0, description="Base Card",
                       required_output_files=["src/Card.tsx"]),
            TicketSpec(id="G0-B", gate=0, description="Base Button",
                       required_output_files=["src/Button.tsx"]),
            TicketSpec(id="G1-P", gate=1, description="Feature parent",
                       depends_on=["G0-A", "G0-B"], is_parent=True),
            TicketSpec(id="G1-A", gate=1, description="Feature child",
                       depends_on=["G0-A"], parent_id="G1-P",
                       required_output_files=["src/Feature.tsx"],
                       interaction_spec="Click button -> modal opens"),
        ])
        result = commit_plan(plan, conn)
        assert result.success, result.errors
        assert result.tickets_created == 4

        # Verify DB
        rows = conn.execute("SELECT id, gate, status FROM tickets ORDER BY id").fetchall()
        assert len(rows) == 4
        assert all(r["status"] == "todo" for r in rows)

        # Verify requirements
        req = conn.execute(
            "SELECT interaction_spec FROM ticket_requirements WHERE ticket_id='G1-A'"
        ).fetchone()
        assert "modal opens" in req["interaction_spec"]

    def test_plan_without_llm_returns_scaffold_only(self):
        plan = generate_decomp_plan(
            prd_text="Some PRD", architecture_text="Some arch",
            project_slug="test", archetype="react-spa",
            llm_fn=None,
        )
        assert len(plan.tickets) >= 5  # scaffold tickets
        assert len(plan.errors) > 0  # warns about no LLM
        # Scaffold includes package.json, vite, tsconfig, html, main
        ids = [t.id for t in plan.tickets]
        assert any("PKG" in i for i in ids)
        assert any("VITE" in i for i in ids)
        assert any("MAIN" in i for i in ids)

    def test_plan_result_is_serializable(self):
        plan = DecompPlan(tickets=[
            TicketSpec(id="T-1", gate=0, description="Test"),
        ])
        d = plan.to_dict()
        json_str = json.dumps(d)
        parsed = json.loads(json_str)
        assert parsed["total_tickets"] == 0  # not computed for manual plans
        assert len(parsed["tickets"]) == 1

    def test_commit_is_idempotent(self, tmp_path):
        """INSERT OR IGNORE means re-committing doesn't duplicate."""
        conn = self._make_db(tmp_path)
        plan = DecompPlan(tickets=[
            TicketSpec(id="T-1", gate=0, description="Test",
                       required_output_files=["f.ts"]),
        ])
        commit_plan(plan, conn)
        commit_plan(plan, conn)  # re-commit
        count = conn.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
        assert count == 1


# ── Check generation tests ────────────────────────────────────────

class TestCheckGeneration:

    def test_generates_check_scripts(self, tmp_path):
        deliverable = tmp_path / "app"
        deliverable.mkdir()
        db_path = tmp_path / "tickets.db"
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        init_db(conn)

        # Insert a ticket with requirements
        conn.execute(
            "INSERT INTO tickets (id, owner, gate, status, parent_ticket_id) VALUES ('T-1','x',0,'todo','P-1')"
        )
        conn.execute(
            """INSERT INTO ticket_requirements (ticket_id, ticket_description,
               required_output_files_json, worker_evidence_json)
               VALUES ('T-1', 'Test', '["src/Card.tsx"]',
                       '["artifacts/T-1.worker.json"]')"""
        )
        conn.commit()

        result = generate_checks(conn, deliverable, tmp_path)
        assert result.success
        assert result.scripts_generated == 1

        # Verify the script exists and contains the right paths
        script = Path(result.generated_paths[0])
        assert script.exists()
        content = script.read_text(encoding="utf-8")
        assert "T-1" in content
        assert "Card.tsx" in content

    def test_skips_tickets_without_files(self, tmp_path):
        deliverable = tmp_path / "app"
        deliverable.mkdir()
        conn = sqlite3.connect(str(tmp_path / "tickets.db"))
        conn.row_factory = sqlite3.Row
        init_db(conn)
        conn.execute("INSERT INTO tickets (id, owner, gate, status) VALUES ('T-1','x',0,'todo')")
        conn.execute(
            "INSERT INTO ticket_requirements (ticket_id, required_output_files_json) VALUES ('T-1', '[]')"
        )
        conn.commit()

        result = generate_checks(conn, deliverable, tmp_path)
        assert result.success
        assert result.scripts_generated == 0
        assert result.scripts_skipped == 1

    def test_generated_paths_resolve_from_config(self, tmp_path):
        """Check scripts use absolute paths — no hardcoded project names."""
        deliverable = tmp_path / "my-app"
        deliverable.mkdir()
        conn = sqlite3.connect(str(tmp_path / "tickets.db"))
        conn.row_factory = sqlite3.Row
        init_db(conn)
        conn.execute("INSERT INTO tickets (id, owner, gate, status, parent_ticket_id) VALUES ('T-1','x',0,'todo','P')")
        conn.execute(
            """INSERT INTO ticket_requirements (ticket_id, required_output_files_json, worker_evidence_json)
               VALUES ('T-1', '["src/X.tsx"]', '["artifacts/T-1.worker.json"]')"""
        )
        conn.commit()

        result = generate_checks(conn, deliverable, tmp_path)
        content = Path(result.generated_paths[0]).read_text(encoding="utf-8")
        # Should contain the absolute deliverable path (possibly escaped)
        deliverable_str = str(deliverable.resolve())
        assert deliverable_str in content or deliverable_str.replace('\\', '\\\\') in content
        # Should NOT contain hardcoded project names
        assert "bumblebee" not in content.lower()
        assert "agent-swarm" not in content.lower()


# ── Full pipeline test ────────────────────────────────────────────

class TestFullPipeline:

    def test_new_project_then_decompose_then_checks(self, tmp_path):
        """Run the full setup pipeline: create → decompose → generate checks."""
        engine_root = tmp_path / "engine"
        engine_root.mkdir()

        # Step 1: Create project
        req = NewProjectRequest(
            slug="pipeline-test",
            display_name="Pipeline Test",
            deliverable_root=str(tmp_path / "app"),
            tech_stack="React + Express",
        )
        proj_result = create_project(req, engine_root, tmp_path)
        assert proj_result.success

        # Step 2: Manual decomposition (no LLM)
        conn = sqlite3.connect(proj_result.db_path)
        conn.row_factory = sqlite3.Row
        plan = DecompPlan(tickets=[
            TicketSpec(id="G0-CARD", gate=0, description="Base Card component",
                       required_output_files=["src/components/base/Card.tsx"],
                       worker_done_criteria="File exists and exports default"),
            TicketSpec(id="G0-BTN", gate=0, description="Base Button component",
                       required_output_files=["src/components/base/Button.tsx"]),
            TicketSpec(id="G1-P", gate=1, description="Library feature",
                       depends_on=["G0-CARD", "G0-BTN"], is_parent=True),
            TicketSpec(id="G1-LIB", gate=1, description="Library panel",
                       depends_on=["G0-CARD"], parent_id="G1-P",
                       required_output_files=["src/components/LibraryPanel.tsx"],
                       interaction_spec="Panel shows file list from /api/library"),
        ])
        decomp_result = commit_plan(plan, conn)
        assert decomp_result.success
        assert decomp_result.tickets_created == 4

        # Step 3: Generate checks
        check_result = generate_checks(
            conn=conn,
            deliverable_root=Path(tmp_path / "app"),
            workspace_root=tmp_path,
        )
        assert check_result.success
        # G0-CARD, G0-BTN, G1-LIB should have checks (G1-P is a parent, no files)
        assert check_result.scripts_generated >= 2

        conn.close()

        # Verify everything is JSON-serializable (dashboard-ready)
        json.dumps(proj_result.to_dict())
        json.dumps(decomp_result.to_dict())
        json.dumps(check_result.to_dict())


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
