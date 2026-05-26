from fastapi import APIRouter, HTTPException
from pathlib import Path
import json
import sqlite3

from ..services.config_loader import get_config

router = APIRouter(tags=["costs"])

# Cloud API pricing (per million tokens, as of 2026)
PRICING = {
    "claude_opus": {"input": 15.0, "output": 75.0, "label": "Claude Opus 4"},
    "gpt4o": {"input": 2.50, "output": 10.0, "label": "GPT-4o"},
}

# Token estimation: conservative averages from real Forge dispatch data
TOKENS_PER_TOOL_CALL_INPUT = 3000
TOKENS_PER_TOOL_CALL_OUTPUT = 1500


@router.get("/costs/{slug}")
async def get_project_costs(slug: str):
    config = get_config()

    # Find project DB and artifacts
    db_paths = config.get("ticketDbPaths", {})
    db_path = db_paths.get(slug)
    if not db_path:
        raise HTTPException(404, f"Project '{slug}' not found")

    db_path = Path(db_path)
    if not db_path.is_absolute():
        # Resolve relative to dashboard root (consistent with start.ps1 Set-Location)
        dashboard_root = Path(__file__).resolve().parent.parent.parent  # dashboard/
        db_path = (dashboard_root / db_path).resolve()

    if not db_path.exists():
        raise HTTPException(404, f"Database not found for '{slug}'")

    # Get project config to find artifacts dir
    project_dir = db_path.parent
    project_config_path = project_dir / "project-config.json"
    artifacts_dir = None
    project_name = slug

    if project_config_path.exists():
        pc = json.loads(project_config_path.read_text(encoding="utf-8"))
        deliverable = pc.get("deliverable_root", "")
        if deliverable:
            dpath = Path(deliverable)
            if not dpath.is_absolute():
                dpath = (project_dir / dpath).resolve()
            artifacts_dir = dpath / "artifacts"
        # Also check artifacts_dir override in config
        arts_override = pc.get("artifacts_dir", "")
        if arts_override:
            apath = Path(arts_override)
            if not apath.is_absolute():
                apath = (project_dir / apath).resolve()
            if apath.exists():
                artifacts_dir = apath
        project_name = pc.get("display_name", slug)

    # Fallback: check for artifacts/ directly in the project dir
    if not artifacts_dir or not artifacts_dir.exists():
        local_arts = project_dir / "artifacts"
        if local_arts.exists():
            artifacts_dir = local_arts

    # Read ticket stats from DB
    conn = sqlite3.connect(str(db_path))
    total_tickets = conn.execute("SELECT count(*) FROM tickets").fetchone()[0]
    completed = conn.execute("SELECT count(*) FROM tickets WHERE status IN ('done', 'qa_verified')").fetchone()[0]
    conn.close()

    # Read worker artifacts for actual stats
    total_duration = 0.0
    total_tool_calls = 0
    total_files = 0
    artifact_count = 0

    if artifacts_dir and artifacts_dir.exists():
        for af in sorted(artifacts_dir.glob("*.worker.json")):
            try:
                data = json.loads(af.read_text(encoding="utf-8"))
                total_duration += data.get("duration_s", 0)
                total_tool_calls += data.get("tool_calls", 0)
                total_files += len(data.get("files_written", []))
                artifact_count += 1
            except (json.JSONDecodeError, OSError):
                continue

    # Estimate tokens
    est_input = total_tool_calls * TOKENS_PER_TOOL_CALL_INPUT
    est_output = total_tool_calls * TOKENS_PER_TOOL_CALL_OUTPUT

    # Calculate cloud costs
    cloud_costs = {}
    for key, pricing in PRICING.items():
        cost = (est_input / 1_000_000) * pricing["input"] + (est_output / 1_000_000) * pricing["output"]
        cloud_costs[key] = round(cost, 2)

    return {
        "project_name": project_name,
        "slug": slug,
        "total_tickets": total_tickets,
        "completed_tickets": completed,
        "total_duration_s": round(total_duration, 1),
        "total_tool_calls": total_tool_calls,
        "total_files_written": total_files,
        "artifact_count": artifact_count,
        "estimated_input_tokens": est_input,
        "estimated_output_tokens": est_output,
        "cloud_costs": cloud_costs,
        "local_cost": 0.0,
        "pricing": PRICING,
    }
