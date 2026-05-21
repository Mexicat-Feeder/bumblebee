"""Tests for the QA pipeline."""
import json
import sqlite3
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from engine.qa import (
    static_check, is_ui_ticket, QAResult,
)
from engine.config import ProjectConfig
from engine.event_log import init_db


def _config(tmp_path):
    return ProjectConfig(
        engine_root=tmp_path / "engine",
        project_root=tmp_path / "project",
        workspace_root=tmp_path,
        deliverable_root=tmp_path / "deliver",
        db_path=tmp_path / "tickets.db",
        artifacts_dir=tmp_path / "deliver" / "artifacts",
        checks_dir=tmp_path / "deliver" / "checks",
        qa_reports_dir=tmp_path / "deliver" / "reports",
        forge_agent="forge",
        models={"forge": "test/m", "vision": "test/m"},
        forge_timeout_seconds=60,
        cycle_interval_seconds=0,
        max_dispatch_attempts=3,
    )


class TestStaticCheck:

    def test_passes_when_files_exist(self, tmp_path):
        cfg = _config(tmp_path)
        (cfg.deliverable_root / "src").mkdir(parents=True)
        (cfg.deliverable_root / "src" / "App.tsx").write_text("x" * 200, encoding="utf-8")
        
        req = {"required_output_files_json": '["src/App.tsx"]'}
        result = static_check("T-1", req, cfg)
        assert result.passed

    def test_fails_when_file_missing(self, tmp_path):
        cfg = _config(tmp_path)
        req = {"required_output_files_json": '["src/Missing.tsx"]'}
        result = static_check("T-1", req, cfg)
        assert not result.passed
        assert "missing" in result.note

    def test_fails_when_file_empty(self, tmp_path):
        cfg = _config(tmp_path)
        (cfg.deliverable_root / "src").mkdir(parents=True)
        (cfg.deliverable_root / "src" / "Empty.tsx").write_text("", encoding="utf-8")
        
        req = {"required_output_files_json": '["src/Empty.tsx"]'}
        result = static_check("T-1", req, cfg)
        assert not result.passed
        assert "empty" in result.note

    def test_fails_when_file_is_stub(self, tmp_path):
        cfg = _config(tmp_path)
        (cfg.deliverable_root / "src").mkdir(parents=True)
        # 50 bytes is below the 150 byte minimum for .tsx
        (cfg.deliverable_root / "src" / "Stub.tsx").write_text("x" * 50, encoding="utf-8")
        
        req = {"required_output_files_json": '["src/Stub.tsx"]'}
        result = static_check("T-1", req, cfg)
        assert not result.passed
        assert "stub" in result.note

    def test_passes_with_no_required_files(self, tmp_path):
        cfg = _config(tmp_path)
        req = {"required_output_files_json": "[]"}
        result = static_check("T-1", req, cfg)
        assert result.passed

    def test_dts_files_use_lower_threshold(self, tmp_path):
        cfg = _config(tmp_path)
        (cfg.deliverable_root / "src").mkdir(parents=True)
        # 10 bytes is above the 5 byte min for .d.ts
        (cfg.deliverable_root / "src" / "vite-env.d.ts").write_text("x" * 10, encoding="utf-8")
        
        req = {"required_output_files_json": '["src/vite-env.d.ts"]'}
        result = static_check("T-1", req, cfg)
        assert result.passed


class TestIsUITicket:

    def test_tsx_is_ui(self):
        assert is_ui_ticket({"required_output_files_json": '["src/App.tsx"]'})

    def test_css_is_ui(self):
        assert is_ui_ticket({"required_output_files_json": '["src/styles.css"]'})

    def test_ts_is_not_ui(self):
        assert not is_ui_ticket({"required_output_files_json": '["src/server.ts"]'})

    def test_mixed_files_is_ui(self):
        assert is_ui_ticket({"required_output_files_json": '["src/api.ts", "src/App.tsx"]'})

    def test_empty_is_not_ui(self):
        assert not is_ui_ticket({"required_output_files_json": "[]"})


class TestNoHardcodedModels:

    def test_qa_module_no_model_strings(self):
        qa_path = Path(__file__).resolve().parents[1] / "qa.py"
        content = qa_path.read_text(encoding="utf-8")
        for pattern in ["qwen", "lemonade/", "kokoro"]:
            assert pattern not in content.lower(), f"Hardcoded '{pattern}' in qa.py"

    def test_screenshot_module_no_model_strings(self):
        ss_path = Path(__file__).resolve().parents[1] / "screenshot.py"
        content = ss_path.read_text(encoding="utf-8")
        for pattern in ["qwen", "lemonade/", "kokoro"]:
            assert pattern not in content.lower(), f"Hardcoded '{pattern}' in screenshot.py"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
