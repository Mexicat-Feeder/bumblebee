"""
Swarm Engine — Config System

All paths derive from a single project-config.json file.
No hardcoded folder names, no hardcoded model names.
Supports {variable} interpolation for paths.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class ConfigError(Exception):
    """Raised when config is invalid or missing required fields."""
    pass


REQUIRED_FIELDS = {
    "engine_root",
    "project_root",
    "workspace_root",
    "deliverable_root",
    "db_path",
    "artifacts_dir",
    "checks_dir",
    "forge_agent",
    "models",
    "forge_timeout_seconds",
    "cycle_interval_seconds",
    "max_dispatch_attempts",
}

REQUIRED_MODEL_KEYS = {"forge", "vision"}

PATH_FIELDS = {
    "engine_root",
    "project_root",
    "workspace_root",
    "deliverable_root",
    "db_path",
    "artifacts_dir",
    "checks_dir",
    "qa_reports_dir",
}


def _interpolate(value: str, variables: dict[str, str]) -> str:
    """Replace {variable} placeholders with resolved values."""
    def replacer(match):
        key = match.group(1)
        if key not in variables:
            raise ConfigError(f"Unknown interpolation variable: {{{key}}}")
        return variables[key]
    return re.sub(r'\{(\w+)\}', replacer, value)


def _interpolate_recursive(obj: Any, variables: dict[str, str]) -> Any:
    """Recursively interpolate all string values in a dict/list."""
    if isinstance(obj, str):
        return _interpolate(obj, variables)
    elif isinstance(obj, dict):
        return {k: _interpolate_recursive(v, variables) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_interpolate_recursive(item, variables) for item in obj]
    return obj


@dataclass(frozen=True)
class UICheckConfig:
    """Configuration for app launch / screenshot / probe."""
    launch_cmd: list[str]
    cwd: str
    url: str
    ui_port: int
    startup_wait_seconds: int = 12
    ui_file_patterns: list[str] = field(default_factory=lambda: [".tsx", ".jsx", ".css"])


@dataclass(frozen=True)
class ProjectConfig:
    """Fully resolved project configuration. All paths are absolute."""
    engine_root: Path
    project_root: Path
    workspace_root: Path
    deliverable_root: Path
    db_path: Path
    artifacts_dir: Path
    checks_dir: Path
    qa_reports_dir: Path

    forge_agent: str
    models: dict[str, str]  # {"forge": "...", "vision": "...", "decomp": "..."}

    forge_timeout_seconds: int
    cycle_interval_seconds: int
    max_dispatch_attempts: int

    ui_check: UICheckConfig | None = None

    # API connection — any OpenAI-compatible endpoint
    api_base_url: str = ""  # e.g. "https://api.openai.com/v1" or "http://localhost:11434/v1"
    api_key: str = ""       # defaults to env BUMBLEBEE_API_KEY or OPENAI_API_KEY

    # Optional fields
    tech_stack: str = ""
    frontend_root: str = "src"
    prd_path: str = ""
    mvp_path: str = ""
    architecture_path: str = ""
    visual_ref: str = ""

    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def forge_model(self) -> str:
        return self.models.get("forge", "")

    @property
    def vision_model(self) -> str:
        return self.models.get("vision", "")

    @property
    def decomp_model(self) -> str:
        return self.models.get("decomp", self.forge_model)

    def get_api_base_url(self) -> str:
        """Resolve API base URL from config, env, or default."""
        if self.api_base_url:
            return self.api_base_url.rstrip("/")
        env = os.environ.get("BUMBLEBEE_API_BASE_URL", "")
        if env:
            return env.rstrip("/")
        return "https://api.openai.com/v1"

    def get_api_key(self) -> str:
        """Resolve API key from config, env vars, or empty."""
        if self.api_key:
            return self.api_key
        return (
            os.environ.get("BUMBLEBEE_API_KEY", "")
            or os.environ.get("OPENAI_API_KEY", "")
        )


def load_config(config_path: str | Path) -> ProjectConfig:
    """Load and validate a project-config.json file."""
    config_path = Path(config_path).resolve()
    if not config_path.exists():
        raise ConfigError(f"Config file not found: {config_path}")

    try:
        raw = json.loads(config_path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as e:
        raise ConfigError(f"Invalid JSON in {config_path}: {e}")

    if not isinstance(raw, dict):
        raise ConfigError(f"Config must be a JSON object, got {type(raw).__name__}")

    # Check required fields
    missing = REQUIRED_FIELDS - set(raw.keys())
    if missing:
        raise ConfigError(f"Missing required config fields: {sorted(missing)}")

    # Check required model keys
    models = raw.get("models", {})
    if not isinstance(models, dict):
        raise ConfigError("'models' must be a dict")
    missing_models = REQUIRED_MODEL_KEYS - set(models.keys())
    if missing_models:
        raise ConfigError(f"Missing required model keys: {sorted(missing_models)}")

    # Build interpolation variables from the raw non-interpolated path fields
    # Order matters: resolve base paths first, then derived paths
    base_vars: dict[str, str] = {}
    for key in ("engine_root", "project_root", "workspace_root", "deliverable_root"):
        val = raw.get(key, "")
        if isinstance(val, str) and "{" not in val:
            base_vars[key] = val

    # Add ui_port if present
    ui_check_raw = raw.get("ui_check", {})
    if isinstance(ui_check_raw, dict) and "ui_port" in ui_check_raw:
        base_vars["ui_port"] = str(ui_check_raw["ui_port"])

    # Interpolate everything
    resolved = _interpolate_recursive(raw, base_vars)

    # Resolve all path fields to absolute
    for key in PATH_FIELDS:
        if key in resolved and isinstance(resolved[key], str):
            resolved[key] = str(Path(resolved[key]).resolve())

    # Build UICheckConfig
    ui_check = None
    ui_raw = resolved.get("ui_check")
    if isinstance(ui_raw, dict) and "launch_cmd" in ui_raw:
        ui_check = UICheckConfig(
            launch_cmd=ui_raw["launch_cmd"],
            cwd=str(Path(ui_raw.get("cwd", resolved.get("deliverable_root", "."))).resolve()),
            url=ui_raw.get("url", "http://127.0.0.1:4177"),
            ui_port=int(ui_raw.get("ui_port", 4177)),
            startup_wait_seconds=int(ui_raw.get("startup_wait_seconds", 12)),
            ui_file_patterns=ui_raw.get("ui_file_patterns", [".tsx", ".jsx", ".css"]),
        )

    # Resolve API settings: support both old (lemonade_api_url) and new (api_base_url) keys
    api_base_url = (
        resolved.get("api_base_url", "")
        or resolved.get("lemonade_api_url", "")  # backwards compat
    )
    api_key = resolved.get("api_key", "")

    return ProjectConfig(
        engine_root=Path(resolved["engine_root"]),
        project_root=Path(resolved["project_root"]),
        workspace_root=Path(resolved["workspace_root"]),
        deliverable_root=Path(resolved["deliverable_root"]),
        db_path=Path(resolved["db_path"]),
        artifacts_dir=Path(resolved["artifacts_dir"]),
        checks_dir=Path(resolved["checks_dir"]),
        qa_reports_dir=Path(resolved.get("qa_reports_dir", str(Path(resolved["deliverable_root"]) / "benchmark-qa" / "reports"))),
        forge_agent=resolved["forge_agent"],
        models=resolved["models"],
        forge_timeout_seconds=int(resolved["forge_timeout_seconds"]),
        cycle_interval_seconds=int(resolved["cycle_interval_seconds"]),
        max_dispatch_attempts=int(resolved["max_dispatch_attempts"]),
        ui_check=ui_check,
        api_base_url=api_base_url,
        api_key=api_key,
        tech_stack=resolved.get("tech_stack", ""),
        frontend_root=resolved.get("frontend_root", "src"),
        prd_path=resolved.get("prd_path", ""),
        mvp_path=resolved.get("mvp_path", ""),
        architecture_path=resolved.get("architecture_path", ""),
        visual_ref=resolved.get("visual_ref", ""),
        raw=raw,
    )
