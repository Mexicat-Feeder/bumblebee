import json, os, sqlite3, logging

log = logging.getLogger(__name__)


def load_projects_json(path: str) -> list[dict]:
    if not os.path.exists(path):
        return []
    with open(path) as f:
        data = json.load(f)
    # Handle both formats: {slug: config, ...} dict or {"projects": [...]} list
    if isinstance(data, dict) and "projects" in data and isinstance(data["projects"], list):
        return data["projects"]
    elif isinstance(data, dict):
        return [{"slug": slug, **info} for slug, info in data.items()]
    elif isinstance(data, list):
        return data
    return []


def get_ticket_counts(db_path: str) -> dict:
    if not os.path.exists(db_path):
        return {"total": 0, "by_status": {}}
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT status, count(*) as n FROM tickets GROUP BY status"
        ).fetchall()
        conn.close()
        by_status = {r["status"]: r["n"] for r in rows}
        return {"total": sum(by_status.values()), "by_status": by_status}
    except Exception as e:
        log.warning("Failed to read tickets from %s: %s", db_path, e)
        return {"total": 0, "by_status": {}, "error": str(e)}
