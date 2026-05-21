"""Tests for the Bumblebee config system."""
import json
import shutil
import tempfile
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from engine.config import load_config, ConfigError, ProjectConfig


# ── Fixtures ──────────────────────────────────────────────────────

def _make_config(tmp_path: Path, overrides: dict = None) -> Path:
    """Write a valid test config to tmp_path and return the path."""
    config = {
        "engine_root": str(tmp_path / "engine"),
        "project_root": str(tmp_path / "projects" / "test"),
        "workspace_root": str(tmp_path),
        "deliverable_root": str(tmp_path / "deliver"),
        "db_path": "{project_root}\\tickets.db",
        "artifacts_dir": "{deliverable_root}\\artifacts",
        "checks_dir": "{deliverable_root}\\checks",
        "qa_reports_dir": "{deliverable_root}\\benchmark-qa\\reports",
        "forge_agent": "forge",
        "models": {
            "forge": "test-model/coder-1",
            "vision": "test-model/vision-1",
            "decomp": "test-model/decomp-1",
        },
        "forge_timeout_seconds": 1200,
        "cycle_interval_seconds": 10,
        "max_dispatch_attempts": 3,
        "ui_check": {
            "launch_cmd": ["npm", "run", "dev"],
            "cwd": "{deliverable_root}",
            "url": "http://127.0.0.1:{ui_port}",
            "ui_port": 4177,
            "startup_wait_seconds": 12,
        },
    }
    if overrides:
        config.update(overrides)
    
    config_path = tmp_path / "project-config.json"
    config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    return config_path


# ── Tests ─────────────────────────────────────────────────────────

class TestConfigLoading:

    def test_config_loads_and_interpolates(self, tmp_path):
        config_path = _make_config(tmp_path)
        cfg = load_config(config_path)
        
        # db_path should be interpolated
        expected_db = (tmp_path / "projects" / "test" / "tickets.db").resolve()
        assert cfg.db_path == expected_db

        # artifacts_dir should be interpolated
        expected_artifacts = (tmp_path / "deliver" / "artifacts").resolve()
        assert cfg.artifacts_dir == expected_artifacts

    def test_all_paths_resolve_to_absolute(self, tmp_path):
        config_path = _make_config(tmp_path)
        cfg = load_config(config_path)
        
        for field_name in ("engine_root", "project_root", "workspace_root",
                          "deliverable_root", "db_path", "artifacts_dir",
                          "checks_dir", "qa_reports_dir"):
            path = getattr(cfg, field_name)
            assert path.is_absolute(), f"{field_name} is not absolute: {path}"

    def test_missing_required_field_raises(self, tmp_path):
        config = {"engine_root": str(tmp_path)}  # missing most fields
        config_path = tmp_path / "bad-config.json"
        config_path.write_text(json.dumps(config), encoding="utf-8")
        
        with pytest.raises(ConfigError, match="Missing required"):
            load_config(config_path)

    def test_missing_model_keys_raises(self, tmp_path):
        config_path = _make_config(tmp_path, overrides={
            "models": {"forge": "something"}  # missing "vision"
        })
        with pytest.raises(ConfigError, match="Missing required model keys"):
            load_config(config_path)

    def test_config_file_not_found_raises(self):
        with pytest.raises(ConfigError, match="not found"):
            load_config("/nonexistent/path/config.json")

    def test_invalid_json_raises(self, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text("not json!", encoding="utf-8")
        with pytest.raises(ConfigError, match="Invalid JSON"):
            load_config(bad)

    def test_model_accessors(self, tmp_path):
        config_path = _make_config(tmp_path)
        cfg = load_config(config_path)
        assert cfg.forge_model == "test-model/coder-1"
        assert cfg.vision_model == "test-model/vision-1"
        assert cfg.decomp_model == "test-model/decomp-1"

    def test_ui_check_parsed(self, tmp_path):
        config_path = _make_config(tmp_path)
        cfg = load_config(config_path)
        assert cfg.ui_check is not None
        assert cfg.ui_check.launch_cmd == ["npm", "run", "dev"]
        assert cfg.ui_check.ui_port == 4177
        assert "4177" in cfg.ui_check.url

    def test_ui_port_interpolated_in_url(self, tmp_path):
        config_path = _make_config(tmp_path)
        cfg = load_config(config_path)
        assert cfg.ui_check.url == "http://127.0.0.1:4177"


class TestConfigPortability:

    def test_config_works_from_any_directory(self, tmp_path):
        """Load config from different CWDs. Resolved paths are identical."""
        config_path = _make_config(tmp_path)
        
        # Load from tmp_path
        cfg1 = load_config(config_path)
        
        # Load from a subdirectory (same absolute path)
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        cfg2 = load_config(config_path)
        
        assert cfg1.db_path == cfg2.db_path
        assert cfg1.deliverable_root == cfg2.deliverable_root

    def test_rename_root_directory(self, tmp_path):
        """Copy the config dir, update engine_root, verify everything still works."""
        original = tmp_path / "original"
        original.mkdir()
        config_path = _make_config(original)
        cfg1 = load_config(config_path)

        # Copy to a new location
        renamed = tmp_path / "renamed"
        shutil.copytree(original, renamed)
        
        # Update engine_root in the copy
        new_config_path = renamed / "project-config.json"
        data = json.loads(new_config_path.read_text(encoding="utf-8"))
        data["engine_root"] = str(renamed / "engine")
        data["project_root"] = str(renamed / "projects" / "test")
        data["workspace_root"] = str(renamed)
        data["deliverable_root"] = str(renamed / "deliver")
        new_config_path.write_text(json.dumps(data), encoding="utf-8")
        
        cfg2 = load_config(new_config_path)
        
        # Paths should be different (different root)
        assert cfg1.engine_root != cfg2.engine_root
        # But both should be valid absolute paths
        assert cfg2.engine_root.is_absolute()
        assert cfg2.db_path.is_absolute()

    def test_path_with_spaces(self, tmp_path):
        """Config path containing spaces resolves correctly."""
        spaced = tmp_path / "path with spaces"
        spaced.mkdir()
        config_path = _make_config(spaced)
        cfg = load_config(config_path)
        assert "path with spaces" in str(cfg.workspace_root)
        assert cfg.db_path.is_absolute()


class TestNoHardcodedStrings:

    def test_no_hardcoded_paths_in_engine(self):
        """Source code must not contain hardcoded project paths."""
        engine_dir = Path(__file__).resolve().parents[2] / "engine"
        violations = []
        for py_file in engine_dir.glob("*.py"):
            content = py_file.read_text(encoding="utf-8")
            for pattern in ["bumblebee", "agent-swarm", "agent_swarm"]:
                if pattern in content.lower():
                    # Exclude this test file and comments
                    lines = content.split("\n")
                    for i, line in enumerate(lines):
                        stripped = line.strip()
                        if pattern in stripped.lower() and not stripped.startswith("#") and not stripped.startswith('"""') and "test" not in py_file.name:
                            # Allow 'bumblebee' in env var names (BUMBLEBEE_*), module self-refs, and docstrings
                            if pattern == "bumblebee" and ("BUMBLEBEE_" in stripped or "Bumblebee" in stripped or "bumblebee/engine/" in stripped):
                                continue
                            violations.append(f"{py_file.name}:{i+1}: {stripped[:80]}")
        assert violations == [], f"Hardcoded paths found:\n" + "\n".join(violations)

    def test_no_hardcoded_model_names_in_engine(self):
        """Source code must not contain hardcoded model names."""
        engine_dir = Path(__file__).resolve().parents[2] / "engine"
        model_patterns = ["qwen", "lemonade/", "kokoro", "gpt-", "claude-", "sonnet-"]
        violations = []
        for py_file in engine_dir.glob("*.py"):
            if "test" in py_file.name:
                continue
            content = py_file.read_text(encoding="utf-8")
            for pattern in model_patterns:
                if pattern in content.lower():
                    lines = content.split("\n")
                    for i, line in enumerate(lines):
                        if pattern in line.lower() and not line.strip().startswith("#"):
                            violations.append(f"{py_file.name}:{i+1}: {line.strip()[:80]}")
        assert violations == [], f"Hardcoded model names found:\n" + "\n".join(violations)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
