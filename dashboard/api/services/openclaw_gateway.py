"""
openclaw_gateway.py — thin client for the OpenClaw gateway /tools/invoke API.
Used to fire the `message` tool (e.g. Telegram) directly from the dashboard backend.
"""
import json
import logging
import os
import urllib.request
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

# Resolve config path: OPENCLAW_CONFIG env var, or the default platform location.
# If the file doesn't exist the gateway features are silently disabled.
_OPENCLAW_CONFIG_PATH = Path(
    os.environ.get(
        "OPENCLAW_CONFIG",
        str(Path.home() / ".openclaw" / "openclaw.json"),
    )
)


def _load_openclaw_config() -> dict:
    if not _OPENCLAW_CONFIG_PATH.exists():
        return {}
    try:
        raw = _OPENCLAW_CONFIG_PATH.read_bytes().decode("utf-8-sig")
        return json.loads(raw)
    except Exception as e:
        log.warning("Could not read openclaw config: %s", e)
        return {}


def _get_gateway_base() -> tuple[str, str]:
    """Return (base_url, token). Reads openclaw.json once per call (fast, small file)."""
    cfg = _load_openclaw_config()
    gw = cfg.get("gateway", {})
    port = gw.get("port", 18789)
    token = gw.get("auth", {}).get("token", "")
    return f"http://127.0.0.1:{port}", token


def invoke_tool(tool: str, args: dict, session_key: str = "main") -> dict:
    """Call POST /tools/invoke on the local gateway. Returns the response dict."""
    base_url, token = _get_gateway_base()
    url = f"{base_url}/tools/invoke"
    payload = json.dumps({"tool": tool, "args": args, "sessionKey": session_key}).encode()
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        log.error("Gateway tool invoke failed (%s): %s", tool, e)
        raise


def send_telegram_message(chat_id: str, message: str) -> bool:
    """Send a Telegram message via OpenClaw gateway. Returns True on success."""
    try:
        result = invoke_tool("message", {
            "action": "send",
            "channel": "telegram",
            "target": chat_id,
            "message": message,
        })
        if result.get("ok"):
            log.info("Telegram message sent to %s", chat_id)
            return True
        log.warning("Telegram send returned not-ok: %s", result)
        return False
    except Exception as e:
        log.error("Failed to send Telegram message: %s", e)
        return False
