from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from pathlib import Path
import logging, shutil

log = logging.getLogger(__name__)
router = APIRouter(tags=["uploads"])

from ..services.registry import get_project, update_project
from ..services.config_loader import get_config


def _uploads_dir(slug: str) -> Path:
    """Resolve the uploads directory for a project.
    Uses intakeUploadsDir from config as base, with slug subdirectory.
    Fallback: bumblebee/projects/{slug}/inputs/ relative to workspace root.
    """
    config = get_config()
    base = config.get("intakeUploadsDir")
    if base:
        p = Path(base) / slug
    else:
        ws = config.get("workspaceRoot", "")
        p = Path(ws) / "bumblebee" / "projects" / slug / "inputs"
    p.mkdir(parents=True, exist_ok=True)
    return p


@router.post("/intake/projects/{slug}/upload/prd")
async def upload_prd(slug: str, file: UploadFile = File(...)):
    project = get_project(slug)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    suffix = Path(file.filename or "prd.md").suffix.lower()
    if suffix not in (".md", ".txt", ".pdf"):
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {suffix}. Use .md, .txt, or .pdf")
    dest = _uploads_dir(slug) / f"prd{suffix}"
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)
    update_project(slug, {"prd_path": str(dest), "checklist": {"prd_uploaded": True}})
    return {"ok": True, "path": str(dest), "filename": file.filename}


@router.post("/intake/projects/{slug}/upload/refs")
async def upload_refs(slug: str, files: list[UploadFile] = File(...)):
    project = get_project(slug)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if len(files) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 reference images")
    allowed = {".png", ".jpg", ".jpeg", ".webp"}
    saved = []
    for i, f in enumerate(files, 1):
        suffix = Path(f.filename or f"ref.png").suffix.lower()
        if suffix not in allowed:
            raise HTTPException(status_code=400, detail=f"Unsupported image type: {suffix}")
        dest = _uploads_dir(slug) / f"ref-{i}{suffix}"
        with open(dest, "wb") as out:
            shutil.copyfileobj(f.file, out)
        saved.append(dest)
    update_project(slug, {"ref_paths": [str(p) for p in saved], "checklist": {"refs_uploaded": True}})
    return {"ok": True, "count": len(saved), "paths": [str(p) for p in saved]}


@router.get("/intake/projects/{slug}/prd")
async def get_prd(slug: str):
    project = get_project(slug)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    prd_path = project.get("prd_path")
    if not prd_path or not Path(prd_path).exists():
        raise HTTPException(status_code=404, detail="PRD file not found")
    return FileResponse(str(prd_path), filename=Path(prd_path).name)


@router.get("/intake/projects/{slug}/refs/{filename}")
async def get_ref_image(slug: str, filename: str):
    project = get_project(slug)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    path = _uploads_dir(slug) / filename
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(str(path))
