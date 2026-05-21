"""
Swarm Engine — Vision Review

Sends screenshots to a vision-capable model for analysis.
Used for:
  - Tier 4 QA (does the screenshot match the interaction spec?)
  - Forge-with-eyes (describe the current app state for next dispatch)

Requires an OpenAI-compatible API endpoint that supports multimodal input.
"""
from __future__ import annotations

import base64
import json
import logging
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any

from .config import ProjectConfig

log = logging.getLogger(__name__)

_CHAT_COMPLETIONS_PATH = "/chat/completions"


def _read_screenshot_b64(screenshot_path: str) -> str | None:
    """Read a screenshot file and return base64-encoded data."""
    p = Path(screenshot_path)
    if not p.exists():
        return None
    with open(p, "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")


def _get_vision_url(config: ProjectConfig) -> str:
    """Get the vision model API URL from config."""
    # Allow a separate vision endpoint, otherwise use the main API URL
    raw = config.raw
    vision_url = raw.get("vision_api_url", "")
    if vision_url:
        return vision_url.rstrip("/")
    return config.get_api_base_url()


def _call_vision(
    url: str,
    model: str,
    image_b64: str,
    prompt: str,
    timeout: int = 120,
    api_key: str = "",
) -> tuple[bool, str]:
    """
    Call the vision model with an image and prompt.
    Returns (success, response_text).
    """
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}},
            {"type": "text", "text": prompt},
        ]}],
        "temperature": 0.1,
        "max_tokens": 2048,
        "stream": False,
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{url}{_CHAT_COMPLETIONS_PATH}",
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read())
            text = data["choices"][0]["message"]["content"].strip()
            return True, text
    except urllib.error.URLError as e:
        return False, f"Vision model unreachable: {e}"
    except Exception as e:
        return False, f"Vision call failed: {e}"


def vision_qa_check(
    screenshot_path: str,
    interaction_spec: str,
    config: ProjectConfig,
) -> tuple[bool, str, str]:
    """
    Tier 4: Vision QA check.
    
    Sends screenshot to vision model with interaction spec as context.
    Returns (passed, note, full_response).
    """
    img_b64 = _read_screenshot_b64(screenshot_path)
    if not img_b64:
        return False, f"Screenshot not found: {screenshot_path}", ""

    url = _get_vision_url(config)
    model = config.vision_model

    prompt = (
        "You are a QA reviewer checking a web application screenshot.\n\n"
        f"Expected behavior:\n{interaction_spec}\n\n"
        "Look at the screenshot and evaluate:\n"
        "1. Does the UI render correctly (not blank, not error screen)?\n"
        "2. Are the expected visual elements present?\n"
        "3. Does the layout match what's described?\n\n"
        "Start your response with PASS or FAIL on the first line, then explain."
    )

    ok, response = _call_vision(url, model, img_b64, prompt, api_key=config.get_api_key())
    if not ok:
        return False, response, ""

    first_line = response.split("\n")[0].strip().upper()
    passed = "PASS" in first_line and "FAIL" not in first_line
    return passed, response[:500], response


def describe_app_state(
    screenshot_path: str,
    config: ProjectConfig,
) -> tuple[bool, str]:
    """
    Forge-with-eyes: describe the current app state for the next dispatch.
    
    Returns (success, description).
    The description is included in the next Forge dispatch contract so
    the model can see what the app currently looks like.
    """
    img_b64 = _read_screenshot_b64(screenshot_path)
    if not img_b64:
        return False, "No screenshot available"

    url = _get_vision_url(config)
    model = config.vision_model

    prompt = (
        "Describe what you see in this web application screenshot in 2-3 sentences. "
        "Focus on: what panels/sections are visible, what content they contain, "
        "what the color scheme is, and any obvious missing or broken elements. "
        "Be specific about component names if visible."
    )

    ok, response = _call_vision(url, model, img_b64, prompt, api_key=config.get_api_key())
    if not ok:
        return False, response

    return True, response.strip()


def get_latest_screenshot_b64(
    config: ProjectConfig,
    ticket_id: str | None = None,
) -> str | None:
    """
    Get the most recent screenshot as base64 for Forge-with-eyes dispatch.
    Looks in artifacts dir for the most recent .screenshot.png file.
    """
    artifacts = config.artifacts_dir
    if not artifacts.exists():
        return None

    # Find most recent screenshot
    screenshots = sorted(
        artifacts.glob("*.screenshot.png"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not screenshots:
        return None

    return _read_screenshot_b64(str(screenshots[0]))
