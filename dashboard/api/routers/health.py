import os
from typing import Any, Dict, List

import httpx
from fastapi import APIRouter

from ..services.config_loader import load_config

router = APIRouter()


async def check_http(name: str, url: str) -> Dict[str, Any]:
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=3.0)
            return {
                "name": name,
                "ok": resp.status_code == 200,
                "detail": f"status={resp.status_code}",
            }
    except Exception as e:
        return {"name": name, "ok": False, "detail": str(e)}


async def check_file(name: str, path: str) -> Dict[str, Any]:
    exists = os.path.exists(path)
    return {
        "name": name,
        "ok": exists,
        "detail": f"path={path}, exists={exists}",
    }


@router.get("/swarm/health")
async def swarm_health() -> Dict[str, Any]:
    """Three named status lights for the header: API, Lemonade, DB."""
    try:
        config = load_config()
    except Exception:
        return {"lights": [{"name": "API", "ok": True}, {"name": "Lemonade", "ok": False}, {"name": "DB", "ok": False}]}

    # API — always ok if this endpoint responds
    api_light = {"name": "API", "ok": True}

    # Lemonade — ping health endpoint
    lemonade_url = config.get("lemonadeUrl", "http://[::1]:13305")
    lemonade_light = await check_http("Lemonade", f"{lemonade_url}/api/v1/health")
    lemonade_light["name"] = "Lemonade"

    # DB — check tickets DB file
    db_paths = config.get("ticketDbPaths", {})
    db_ok = any(os.path.exists(p) for p in db_paths.values())
    db_light = {"name": "DB", "ok": db_ok}

    lights = [api_light, lemonade_light, db_light]
    return {"lights": lights, "ok": all(l["ok"] for l in lights)}


@router.get("/health")
async def health() -> Dict[str, Any]:
    try:
        config = load_config()
    except Exception:
        return {"ok": False, "services": [], "error": "config not found"}

    health_checks = config.get("healthChecks", [])
    if not health_checks:
        return {"ok": True, "services": []}

    results: List[Dict[str, Any]] = []

    for check in health_checks:
        check_type = check.get("type", "")
        name = check.get("name", "unknown")

        if check_type == "http":
            url = check.get("url", "")
            results.append(await check_http(name, url))
        elif check_type == "file":
            path = check.get("path", "")
            results.append(await check_file(name, path))
        else:
            results.append({"name": name, "ok": False, "detail": f"unknown check type: {check_type}"})

    all_ok = all(r["ok"] for r in results)
    return {"ok": all_ok, "services": results}
