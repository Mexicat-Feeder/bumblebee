"""
Cloud API usage tracker for Bumblebee.

Tracks token usage and estimated costs from cloud model calls
(decompose, integration). Stored as a simple JSON file in the
project directory so the dashboard can display it.
"""
import json
import logging
import time
from pathlib import Path
from threading import Lock

log = logging.getLogger(__name__)

_lock = Lock()

# Pricing per million tokens (as of 2026)
PRICING = {
    "gpt-5.5": {"input": 3.00, "output": 12.00},
    "gpt-5.4": {"input": 1.25, "output": 5.00},
    "gpt-5.4-mini": {"input": 0.15, "output": 0.60},
    "gpt-4.1-mini": {"input": 0.10, "output": 0.40},
    "gpt-4o": {"input": 2.50, "output": 10.00},
}

# Default storage path (can be overridden)
_DEFAULT_PATH = None


def _get_path(project_dir: str | Path | None = None) -> Path:
    """Get the usage file path."""
    if project_dir:
        return Path(project_dir) / "cloud-usage.json"
    if _DEFAULT_PATH:
        return Path(_DEFAULT_PATH)
    # Fallback to bumblebee root
    return Path(__file__).resolve().parent.parent / "cloud-usage.json"


def _load(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {
        "model": "",
        "provider": "openai",
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_read_tokens": 0,
        "total_tokens": 0,
        "estimated_cost_usd": 0.0,
        "calls": 0,
        "started_at": time.time(),
        "updated_at": time.time(),
        "phases": {},
    }


def _save(path: Path, data: dict) -> None:
    data["updated_at"] = time.time()
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(path)


def record_usage(
    model: str,
    usage: dict,
    phase: str = "unknown",
    project_dir: str | Path | None = None,
) -> None:
    """Record token usage from a cloud API response.
    
    Args:
        model: Model ID (e.g. "gpt-5.5")
        usage: The 'usage' dict from the API response
        phase: Phase name (e.g. "decompose", "integration")
        project_dir: Project directory for storage
    """
    if not usage:
        return

    input_tokens = usage.get("prompt_tokens", 0) or 0
    output_tokens = usage.get("completion_tokens", 0) or 0
    cache_read = usage.get("prompt_tokens_details", {}).get("cached_tokens", 0) or 0
    total = input_tokens + output_tokens

    # Calculate cost
    pricing = PRICING.get(model, PRICING.get("gpt-5.5"))
    cost = (input_tokens / 1_000_000) * pricing["input"] + \
           (output_tokens / 1_000_000) * pricing["output"]

    path = _get_path(project_dir)
    with _lock:
        data = _load(path)
        data["model"] = model
        data["provider"] = "openai"
        data["input_tokens"] += input_tokens
        data["output_tokens"] += output_tokens
        data["cache_read_tokens"] += cache_read
        data["total_tokens"] += total
        data["estimated_cost_usd"] = round(data["estimated_cost_usd"] + cost, 6)
        data["calls"] += 1

        # Per-phase tracking
        p = data.setdefault("phases", {}).setdefault(phase, {
            "input_tokens": 0, "output_tokens": 0, "calls": 0, "cost_usd": 0.0
        })
        p["input_tokens"] += input_tokens
        p["output_tokens"] += output_tokens
        p["calls"] += 1
        p["cost_usd"] = round(p["cost_usd"] + cost, 6)

        _save(path, data)

    log.info(
        "Cloud usage [%s/%s]: +%d in, +%d out, $%.4f (total $%.4f)",
        phase, model, input_tokens, output_tokens, cost, data["estimated_cost_usd"]
    )


def reset_usage(project_dir: str | Path | None = None) -> None:
    """Reset usage counters (called on demo reset)."""
    path = _get_path(project_dir)
    with _lock:
        if path.exists():
            path.unlink()


def get_usage(project_dir: str | Path | None = None) -> dict:
    """Get current usage data."""
    path = _get_path(project_dir)
    with _lock:
        return _load(path)
