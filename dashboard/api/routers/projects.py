from fastapi import APIRouter
from ..services.config_loader import get_config
from ..services.project_loader import load_projects_json, get_ticket_counts

router = APIRouter(tags=["projects"])


@router.get("/projects")
async def list_projects():
    config = get_config()
    return {"projects": load_projects_json(config["projectsJsonPath"])}


@router.get("/projects/{slug}")
async def project_detail(slug: str):
    config = get_config()
    db_paths = config.get("ticketDbPaths", {})
    if slug not in db_paths:
        return {"error": f"Unknown project: {slug}"}
    return {"slug": slug, "ticket_counts": get_ticket_counts(db_paths[slug])}


@router.patch("/projects/queue-order")
async def reorder_queue(order: list[str]):
    return {"ok": True, "order": order}
