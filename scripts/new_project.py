"""
Swarm Engine — New Project Setup

Creates a project scaffold: directory structure, config, DB, and
registers it in the projects index.

Designed as importable functions for both CLI and future dashboard use.
Every function takes structured input and returns structured output.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Add engine to path
_ENGINE_ROOT = Path(__file__).resolve().parents[1] / "engine"
sys.path.insert(0, str(_ENGINE_ROOT.parent))

from engine.event_log import init_db
from engine.config import load_config, ProjectConfig


# ---------------------------------------------------------------------------
# Data structures (dashboard-friendly)
# ---------------------------------------------------------------------------

@dataclass
class NewProjectRequest:
    """Input for creating a new project. A dashboard form would produce this."""
    slug: str
    display_name: str
    deliverable_root: str           # where app code lives (e.g. ./output/my-app)
    tech_stack: str                 # e.g. "TypeScript/React frontend, Express backend"
    ui_port: int = 4177
    prd_path: str = ""              # path to PRD markdown
    mvp_path: str = ""              # path to MVP markdown
    visual_ref_path: str = ""       # path to visual reference image
    archetype: str = "react-spa"    # project archetype
    lanes: list[str] = field(default_factory=lambda: ["default"])
    frontend_root: str = "src"
    launch_cmd: list[str] = field(default_factory=lambda: ["npm", "run", "dev"])


@dataclass
class NewProjectResult:
    """Output from project creation. Dashboard can display this."""
    success: bool
    project_root: str = ""
    config_path: str = ""
    db_path: str = ""
    errors: list[str] = field(default_factory=list)
    files_created: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "project_root": self.project_root,
            "config_path": self.config_path,
            "db_path": self.db_path,
            "errors": self.errors,
            "files_created": self.files_created,
        }


# ---------------------------------------------------------------------------
# Projects index
# ---------------------------------------------------------------------------

def _projects_index_path(engine_root: Path) -> Path:
    return engine_root.parent / "projects" / "projects.json"


def _load_projects_index(engine_root: Path) -> dict:
    path = _projects_index_path(engine_root)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8-sig"))
    return {"projects": []}


def _save_projects_index(engine_root: Path, index: dict) -> None:
    path = _projects_index_path(engine_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Core function
# ---------------------------------------------------------------------------

def create_project(
    request: NewProjectRequest,
    engine_root: Path,
    workspace_root: Path,
) -> NewProjectResult:
    """
    Create a new project scaffold.
    
    This is the function a dashboard would call.
    Returns structured result — no prints, no sys.exit.
    """
    result = NewProjectResult(success=False)
    errors = result.errors

    # Validate
    if not request.slug or not request.slug.strip():
        errors.append("slug is required")
        return result
    slug = request.slug.strip()

    if not request.deliverable_root:
        errors.append("deliverable_root is required")
        return result

    deliverable_root = Path(request.deliverable_root).resolve()
    projects_base = engine_root.parent / "projects"
    project_root = projects_base / slug

    # Check for existing project
    index = _load_projects_index(engine_root)
    existing_slugs = {p["slug"] for p in index.get("projects", [])}
    if slug in existing_slugs:
        errors.append(f"Project '{slug}' already exists in projects index")
        return result

    # Create directories
    try:
        project_root.mkdir(parents=True, exist_ok=True)
        deliverable_root.mkdir(parents=True, exist_ok=True)
        (deliverable_root / "artifacts").mkdir(exist_ok=True)
        (deliverable_root / "checks" / "worker").mkdir(parents=True, exist_ok=True)
        (deliverable_root / "checks" / "qa").mkdir(parents=True, exist_ok=True)
        (deliverable_root / "benchmark-qa" / "reports").mkdir(parents=True, exist_ok=True)
        (deliverable_root / request.frontend_root).mkdir(parents=True, exist_ok=True)

        result.files_created.append(str(project_root))
        result.files_created.append(str(deliverable_root))
    except OSError as e:
        errors.append(f"Failed to create directories: {e}")
        return result

    # Copy visual reference if provided
    if request.visual_ref_path:
        vis_src = Path(request.visual_ref_path)
        if vis_src.exists():
            vis_dir = project_root / "visual-refs"
            vis_dir.mkdir(exist_ok=True)
            vis_dst = vis_dir / vis_src.name
            shutil.copy2(vis_src, vis_dst)
            result.files_created.append(str(vis_dst))

    # Build project config
    config_data = {
        "engine_root": str(engine_root),
        "project_root": str(project_root),
        "workspace_root": str(workspace_root),
        "deliverable_root": str(deliverable_root),
        "db_path": str(project_root / "tickets.db"),
        "artifacts_dir": str(deliverable_root / "artifacts"),
        "checks_dir": str(deliverable_root / "checks"),
        "qa_reports_dir": str(deliverable_root / "benchmark-qa" / "reports"),
        "forge_agent": "forge",
        "models": {
            "forge": "",    # set by operator before running
            "vision": "",   # set by operator before running
            "decomp": "",   # set by operator before running
        },
        "forge_timeout_seconds": 1200,
        "cycle_interval_seconds": 10,
        "max_dispatch_attempts": 3,
        "tech_stack": request.tech_stack,
        "frontend_root": request.frontend_root,
        "prd_path": request.prd_path,
        "mvp_path": request.mvp_path,
        "visual_ref": request.visual_ref_path,
        "architecture_path": str(project_root / "ARCHITECTURE.md"),
        "archetype": request.archetype,
        "display_name": request.display_name,
        "ui_check": {
            "launch_cmd": request.launch_cmd,
            "cwd": str(deliverable_root),
            "url": f"http://127.0.0.1:{request.ui_port}",
            "ui_port": request.ui_port,
            "startup_wait_seconds": 12,
            "ui_file_patterns": [".tsx", ".jsx", ".vue", ".svelte", ".css"],
        },
        "lane_cwds": {lane: str(deliverable_root) for lane in request.lanes},
        "loops_enabled": False,
    }

    config_path = project_root / "project-config.json"
    config_path.write_text(json.dumps(config_data, indent=2) + "\n", encoding="utf-8")
    result.files_created.append(str(config_path))
    result.config_path = str(config_path)

    # Write scaffold files from archetype template
    from engine.templates import REACT_SPA_TEMPLATES, write_scaffold_files
    if request.archetype in ("react-spa", "react-express"):
        variables = {
            "slug": slug,
            "port": str(request.ui_port),
            "title": request.display_name or slug,
        }
        scaffold_files = write_scaffold_files(deliverable_root, REACT_SPA_TEMPLATES, variables)
        result.files_created.extend(scaffold_files)

    # Initialize DB
    db_path = project_root / "tickets.db"
    try:
        conn = sqlite3.connect(str(db_path))
        init_db(conn)
        conn.close()
        result.files_created.append(str(db_path))
        result.db_path = str(db_path)
    except Exception as e:
        errors.append(f"Failed to initialize DB: {e}")
        return result

    # Register in projects index
    index["projects"].append({
        "slug": slug,
        "display_name": request.display_name,
        "root": str(project_root),
        "deliverable_root": str(deliverable_root),
        "archetype": request.archetype,
        "active": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    _save_projects_index(engine_root, index)

    result.success = True
    result.project_root = str(project_root)
    return result


# ---------------------------------------------------------------------------
# CLI wrapper
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Create a new swarm project")
    parser.add_argument("--slug", required=True, help="Project slug (e.g. remy)")
    parser.add_argument("--name", required=True, help="Display name")
    parser.add_argument("--deliverable-root", required=True, help="Path for app code")
    parser.add_argument("--tech-stack", default="TypeScript/React frontend, Express backend")
    parser.add_argument("--port", type=int, default=4177)
    parser.add_argument("--prd", default="", help="Path to PRD markdown")
    parser.add_argument("--mvp", default="", help="Path to MVP markdown")
    parser.add_argument("--visual-ref", default="", help="Path to visual reference image")
    parser.add_argument("--archetype", default="react-spa")
    parser.add_argument("--engine-root", default=str(_ENGINE_ROOT))
    parser.add_argument("--workspace-root", default=str(Path.cwd()))
    args = parser.parse_args()

    request = NewProjectRequest(
        slug=args.slug,
        display_name=args.name,
        deliverable_root=args.deliverable_root,
        tech_stack=args.tech_stack,
        ui_port=args.port,
        prd_path=args.prd,
        mvp_path=args.mvp,
        visual_ref_path=args.visual_ref,
        archetype=args.archetype,
    )

    result = create_project(
        request=request,
        engine_root=Path(args.engine_root),
        workspace_root=Path(args.workspace_root),
    )

    print(json.dumps(result.to_dict(), indent=2))
    return 0 if result.success else 1


if __name__ == "__main__":
    sys.exit(main())
