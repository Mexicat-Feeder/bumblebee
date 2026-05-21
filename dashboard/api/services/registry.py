from pathlib import Path
import json, os, logging, threading
from datetime import datetime, timezone

log = logging.getLogger(__name__)

_lock = threading.Lock()


def _registry_path() -> Path:
    """Read registryPath from dashboard config. Fallback to 'data/registry.json' relative to project root."""
    from .config_loader import get_config
    config = get_config()
    p = config.get("registryPath", "data/registry.json")
    if not os.path.isabs(p):
        # Project root is two levels up from services/ (services -> dashboard-api -> project root)
        p = str(Path(__file__).resolve().parent.parent.parent / p)
    return Path(p)


def _read() -> list[dict]:
    path = _registry_path()
    if not path.exists():
        return []
    with open(path) as f:
        data = json.load(f)
    if isinstance(data, dict) and "projects" in data:
        return data["projects"]
    return []


def _write(projects: list[dict]) -> None:
    path = _registry_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w") as f:
        json.dump({"projects": projects}, f, indent=2)
    tmp.replace(path)


def list_projects() -> list[dict]:
    with _lock:
        return _read()


def get_project(slug: str) -> dict | None:
    with _lock:
        for p in _read():
            if p["slug"] == slug:
                return p
    return None


def create_project(name: str, slug: str, description: str, deliverable_root: str, target_system: str = "local") -> dict:
    project = {
        "slug": slug,
        "name": name,
        "description": description,
        "deliverable_root": deliverable_root,
        "target_system": target_system,
        "status": "intake",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "prd_path": None,
        "ref_paths": [],
        "tech_stack": None,
        "visual_spec_path": None,
        "architecture_path": None,
        "checklist": {
            "named": True,
            "prd_uploaded": False,
            "refs_uploaded": False,
            "qa_complete": False,
            "approved": False,
            "scaffolded": False,
            "running": False
        }
    }
    with _lock:
        projects = _read()
        if any(p["slug"] == slug for p in projects):
            raise ValueError(f"Project '{slug}' already exists")
        projects.append(project)
        _write(projects)
    return project


def update_project(slug: str, updates: dict) -> dict | None:
    with _lock:
        projects = _read()
        for p in projects:
            if p["slug"] == slug:
                # Merge top-level fields
                for k, v in updates.items():
                    if k == "checklist" and isinstance(v, dict):
                        p.setdefault("checklist", {}).update(v)
                    else:
                        p[k] = v
                _write(projects)
                return p
    return None
