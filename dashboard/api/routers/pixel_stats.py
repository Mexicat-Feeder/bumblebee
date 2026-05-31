import json
import os
import logging
from fastapi import APIRouter
from ..services.config_loader import get_config

log = logging.getLogger(__name__)
router = APIRouter(tags=["pixel"])

# Default is empty; configure via OPENCLAW_SESSIONS_PATH env var or "pixelSessionsPath" in dashboard.config.json
_DEFAULT_SESSIONS_PATH = os.environ.get("OPENCLAW_SESSIONS_PATH", "")
_TELEGRAM_SESSION_KEY = "agent:main:telegram:direct:8796170855"


def _load_sessions(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        log.warning("Failed to read sessions: %s", e)
        return {}


@router.get("/pixel/stats")
def pixel_stats():
    config = get_config()
    project_start = config.get("pixelProjectStart", None)

    # Try local cloud-usage.json first (tracks decompose + integration calls)
    bumblebee_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    usage_path = os.path.join(bumblebee_root, "cloud-usage.json")

    # Also check demos/food-cart/ for project-specific usage
    if not os.path.exists(usage_path):
        for candidate in ["demos/food-cart/cloud-usage.json", "projects/food-cart/cloud-usage.json"]:
            p = os.path.join(bumblebee_root, candidate)
            if os.path.exists(p):
                usage_path = p
                break

    if os.path.exists(usage_path):
        try:
            with open(usage_path, "r", encoding="utf-8") as f:
                usage = json.load(f)
            return {
                "available": True,
                "model": usage.get("model", "gpt-5.5"),
                "modelRaw": usage.get("model", "gpt-5.5"),
                "provider": usage.get("provider", "openai"),
                "inputTokens": usage.get("input_tokens", 0),
                "outputTokens": usage.get("output_tokens", 0),
                "cacheRead": usage.get("cache_read_tokens", 0),
                "cacheWrite": 0,
                "totalTokens": usage.get("total_tokens", 0),
                "contextTokens": 1000000,
                "estimatedCostUsd": round(usage.get("estimated_cost_usd", 0), 4),
                "sessionStartedAt": usage.get("started_at"),
                "projectStart": project_start,
                "phases": usage.get("phases", {}),
            }
        except Exception as e:
            log.warning("Failed to read cloud usage: %s", e)

    # Fallback to OpenClaw session data (for Gopo where Pixel runs)
    sessions_path = config.get("pixelSessionsPath", _DEFAULT_SESSIONS_PATH)
    sessions = _load_sessions(sessions_path)
    if not sessions:
        return {"available": False}

    session = sessions.get(_TELEGRAM_SESSION_KEY, {})
    if not session or not session.get("totalTokens"):
        candidates = [
            s for s in sessions.values()
            if isinstance(s, dict) and s.get("totalTokens") and s.get("modelProvider")
        ]
        if candidates:
            session = max(candidates, key=lambda s: s.get("updatedAt", 0))

    if not session:
        return {"available": False}

    model_raw = session.get("model", "unknown")
    provider = session.get("modelProvider", "unknown")
    model_display = model_raw
    if "claude" in model_raw:
        import re
        cleaned = re.sub(r'(\d+)-(\d+)$', r'\1.\2', model_raw)
        model_display = cleaned.replace("claude-", "Claude ").replace("-", " ").title()

    return {
        "available": True,
        "model": model_display,
        "modelRaw": model_raw,
        "provider": provider,
        "inputTokens": session.get("inputTokens", 0) or 0,
        "outputTokens": session.get("outputTokens", 0) or 0,
        "cacheRead": session.get("cacheRead", 0) or 0,
        "cacheWrite": session.get("cacheWrite", 0) or 0,
        "totalTokens": session.get("totalTokens", 0) or 0,
        "contextTokens": session.get("contextTokens", 1000000) or 1000000,
        "estimatedCostUsd": round(session.get("estimatedCostUsd", 0) or 0, 4),
        "sessionStartedAt": session.get("sessionStartedAt"),
        "projectStart": project_start,
    }
