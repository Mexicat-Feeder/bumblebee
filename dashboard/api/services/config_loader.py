import json
import os
from pathlib import Path

_config = None


def load_config() -> dict:
    global _config
    if _config is not None:
        return _config
    config_path = os.environ.get("DASHBOARD_CONFIG", "dashboard.config.json")
    # Resolve relative paths from the project root (parent of dashboard-api/)
    if not os.path.isabs(config_path):
        config_path = str(Path(__file__).resolve().parent.parent / config_path)
    with open(config_path) as f:
        _config = json.load(f)
    return _config


def get_config() -> dict:
    return load_config()
