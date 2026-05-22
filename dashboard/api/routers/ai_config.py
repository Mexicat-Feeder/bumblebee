"""
AI Configuration — model selection and API settings.

Endpoints:
  GET  /api/ai/models  — probe Lemonade + return available models
  GET  /api/ai/config  — current global AI defaults
  PATCH /api/ai/config — update global AI defaults
"""
from __future__ import annotations

import logging
import os
from typing import Optional

import httpx
from fastapi import APIRouter
from pydantic import BaseModel

from ..services.config_loader import get_config, save_config

log = logging.getLogger(__name__)
router = APIRouter(prefix="/ai", tags=["ai"])

# Default Lemonade URL — IPv6 loopback, port 13305
DEFAULT_LEMONADE_URL = "http://[::1]:13305"


# ---------------------------------------------------------------------------
# Models endpoint — probe Lemonade for available models
# ---------------------------------------------------------------------------

@router.get("/models")
async def list_models():
    """
    Probe Lemonade (or configured local AI server) for available models.
    Returns a structured list of models with their capabilities.
    """
    config = get_config()
    ai_config = config.get("ai", {})
    lemonade_url = ai_config.get("lemonade_url", DEFAULT_LEMONADE_URL)

    result = {
        "lemonade": {
            "url": lemonade_url,
            "connected": False,
            "models": [],
        }
    }

    try:
        async with httpx.AsyncClient() as client:
            # Probe /v1/models (OpenAI-compatible)
            resp = await client.get(
                f"{lemonade_url}/v1/models",
                timeout=5.0,
            )
            if resp.status_code == 200:
                data = resp.json()
                models_raw = data.get("data", [])
                models = []
                for m in models_raw:
                    model_id = m.get("id", "")
                    labels = m.get("labels", [])
                    recipe = m.get("recipe", "")
                    # Skip TTS models
                    if recipe == "kokoro":
                        continue
                    models.append({
                        "id": model_id,
                        "name": _clean_model_name(model_id),
                        "loaded": "hot" in labels,
                        "labels": labels,
                    })
                result["lemonade"]["connected"] = True
                result["lemonade"]["models"] = models
    except Exception as e:
        log.debug("Lemonade probe failed: %s", e)

    return result


def _clean_model_name(model_id: str) -> str:
    """Convert 'Qwen3.6-35B-A3B-GGUF' → 'Qwen3.6 35B'"""
    import re
    name = re.sub(
        r'-(A\d+B|GGUF|Instruct|UD|Q\d.*|FLM).*$', '',
        model_id, flags=re.IGNORECASE,
    )
    return name.replace("-", " ").strip()


# ---------------------------------------------------------------------------
# Config endpoints — global AI defaults
# ---------------------------------------------------------------------------

class AIConfigUpdate(BaseModel):
    lemonade_url: Optional[str] = None
    # Per-phase model config
    qa_model_source: Optional[str] = None      # "lemonade" | "custom"
    qa_model_id: Optional[str] = None
    decomp_model_source: Optional[str] = None   # "lemonade" | "custom"
    decomp_model_id: Optional[str] = None
    forge_model_source: Optional[str] = None     # "lemonade" | "custom"
    forge_model_id: Optional[str] = None
    vision_model_source: Optional[str] = None    # "lemonade" | "custom"
    vision_model_id: Optional[str] = None
    # Custom API settings (used when source is "custom")
    custom_api_base_url: Optional[str] = None
    custom_api_key: Optional[str] = None


@router.get("/config")
def get_ai_config():
    """Return current global AI configuration defaults."""
    config = get_config()
    ai = config.get("ai", {})
    return {
        "lemonade_url": ai.get("lemonade_url", DEFAULT_LEMONADE_URL),
        "qa_model_source": ai.get("qa_model_source", "lemonade"),
        "qa_model_id": ai.get("qa_model_id", ""),
        "decomp_model_source": ai.get("decomp_model_source", "lemonade"),
        "decomp_model_id": ai.get("decomp_model_id", ""),
        "forge_model_source": ai.get("forge_model_source", "custom"),
        "forge_model_id": ai.get("forge_model_id", ""),
        "vision_model_source": ai.get("vision_model_source", "custom"),
        "vision_model_id": ai.get("vision_model_id", ""),
        "custom_api_base_url": ai.get("custom_api_base_url", ""),
        "custom_api_key": _mask_key(ai.get("custom_api_key", "")),
        "has_custom_api_key": bool(ai.get("custom_api_key", "")),
    }


@router.patch("/config")
def update_ai_config(body: AIConfigUpdate):
    """Update global AI defaults. Persists to dashboard.config.json."""
    config = get_config()
    ai = config.setdefault("ai", {})

    updates = body.model_dump(exclude_none=True)
    for key, value in updates.items():
        ai[key] = value

    save_config(config)
    log.info("AI config updated: %s", list(updates.keys()))

    return get_ai_config()


def _mask_key(key: str) -> str:
    """Mask an API key for display: sk-abc...xyz"""
    if not key or len(key) < 8:
        return "••••••••" if key else ""
    return f"{key[:6]}...{key[-4:]}"
