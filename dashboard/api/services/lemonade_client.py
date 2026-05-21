import httpx, os, time, math, logging, re

log = logging.getLogger(__name__)

_cache: dict = {}
_cache_time: float = 0
CACHE_TTL = 1.0

# Peak tracking — persists for the backend process lifetime
_peaks: dict = {
    "tokens_per_second": None,
    "npu_utilization": None,
}
_last_live: dict = {}  # Last known good values when Lemonade was reachable


def _mock_data() -> dict:
    t = time.time()
    return {
        "is_live": True,
        "tokens_per_second": round(25 + 15 * math.sin(t / 4), 1),
        "time_to_first_token": round(0.3 + 0.2 * math.sin(t / 7), 3),
        "npu_utilization": round(40 + 20 * math.sin(t / 5), 1),
        "input_tokens": 1200,
        "output_tokens": 980,
        "active_model": "Qwen3.6 35B",
        "active_model_raw": "Qwen3.6-35B-A3B-GGUF",
        "peak_tokens_per_second": 48.5,
        "peak_npu_utilization": 62.0,
    }


def _clean_model_name(model_id: str) -> str:
    """Convert 'Qwen3.6-35B-A3B-GGUF' → 'Qwen3.6 35B'"""
    # Strip suffixes like -A3B-GGUF, -Instruct-GGUF, etc.
    name = re.sub(r'-(A\d+B|GGUF|Instruct|UD|Q\d.*|FLM).*$', '', model_id, flags=re.IGNORECASE)
    # Clean up remaining hyphens
    name = name.replace("-", " ").strip()
    return name


def _pick_active_model(models_data: dict) -> tuple[str, str]:
    """Pick the active (hot) non-TTS model. Returns (display_name, raw_id)."""
    models = models_data.get("data", [])
    # Prefer "hot" + not TTS
    for m in models:
        labels = m.get("labels", [])
        if "hot" in labels and m.get("recipe") != "kokoro":
            raw = m.get("id", "")
            return _clean_model_name(raw), raw
    # Fallback: first non-TTS model
    for m in models:
        if m.get("recipe") != "kokoro":
            raw = m.get("id", "")
            return _clean_model_name(raw), raw
    return "Unknown", ""


async def get_inference_metrics(lemonade_url: str) -> dict:
    global _cache, _cache_time, _peaks, _last_live
    now = time.time()
    if now - _cache_time < CACHE_TTL and _cache:
        return _cache

    if os.environ.get("MOCK_TELEMETRY") == "1":
        _cache = _mock_data()
        _cache_time = now
        return _cache

    result = {"is_live": False}
    try:
        async with httpx.AsyncClient() as client:
            # Stats
            resp = await client.get(f"{lemonade_url}/api/v1/stats", timeout=3.0)
            if resp.status_code == 200:
                stats = resp.json()
                result["tokens_per_second"] = stats.get("tokens_per_second")
                result["time_to_first_token"] = stats.get("time_to_first_token")
                result["input_tokens"] = stats.get("input_tokens") or stats.get("prompt_tokens")
                result["output_tokens"] = stats.get("output_tokens")

            # System info (NPU)
            resp2 = await client.get(f"{lemonade_url}/api/v1/system-info", timeout=3.0)
            if resp2.status_code == 200:
                info = resp2.json()
                npu = info.get("devices", {}).get("amd_npu", {})
                result["npu_utilization"] = npu.get("utilization")

            # Active model — use /api/v1/health which returns model_loaded directly
            resp3 = await client.get(f"{lemonade_url}/api/v1/health", timeout=3.0)
            if resp3.status_code == 200:
                health = resp3.json()
                raw = health.get("model_loaded", "")
                result["active_model"] = _clean_model_name(raw) if raw else "Unknown"
                result["active_model_raw"] = raw

        result["is_live"] = True

        # Update peaks
        tps = result.get("tokens_per_second")
        if tps and (_peaks["tokens_per_second"] is None or tps > _peaks["tokens_per_second"]):
            _peaks["tokens_per_second"] = round(tps, 1)
        npu = result.get("npu_utilization")
        if npu and (_peaks["npu_utilization"] is None or npu > _peaks["npu_utilization"]):
            _peaks["npu_utilization"] = round(npu, 1)

        _last_live = dict(result)

    except Exception as e:
        log.debug("Lemonade query failed: %s", e)
        if _last_live:
            result = dict(_last_live)
            result["is_live"] = False

    # Fall back to last_live values as peaks if backend restarted with no history
    peak_tps = _peaks.get("tokens_per_second")
    if peak_tps is None and _last_live.get("tokens_per_second"):
        peak_tps = round(_last_live["tokens_per_second"], 1)

    peak_npu = _peaks.get("npu_utilization")
    if peak_npu is None and _last_live.get("npu_utilization"):
        peak_npu = round(_last_live["npu_utilization"], 1)

    result["peak_tokens_per_second"] = peak_tps
    result["peak_npu_utilization"] = peak_npu

    _cache = result
    _cache_time = now
    return result
