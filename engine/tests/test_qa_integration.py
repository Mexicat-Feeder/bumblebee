"""
Integration tests for QA Tiers 2-3 against a real running app.

Uses the test-app fixture (React + Vite on port 4199).
Tests: port kill, app launch, screenshot capture, functional probe,
       process cleanup, E2E test execution.
"""
import json
import os
import sqlite3
import subprocess
import time
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from engine.screenshot import kill_port, is_port_free, launch_app, kill_app, take_screenshot
from engine.qa import functional_probe, static_check, e2e_test, QAResult
from engine.config import ProjectConfig, UICheckConfig
from engine.event_log import init_db

TEST_APP_DIR = Path(__file__).resolve().parent / "fixtures" / "test-app"
TEST_PORT = 4199


@pytest.fixture(autouse=True)
def clean_port():
    """Ensure port is free before and after each test."""
    kill_port(TEST_PORT)
    time.sleep(0.5)
    yield
    kill_port(TEST_PORT)
    time.sleep(0.5)


@pytest.fixture
def config(tmp_path):
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()
    return ProjectConfig(
        engine_root=tmp_path / "engine",
        project_root=tmp_path / "project",
        workspace_root=tmp_path,
        deliverable_root=tmp_path / "deliver",
        db_path=tmp_path / "tickets.db",
        artifacts_dir=artifacts,
        checks_dir=tmp_path / "checks",
        qa_reports_dir=tmp_path / "reports",
        forge_agent="forge",
        models={"forge": "test/m", "vision": "test/m"},
        forge_timeout_seconds=60,
        cycle_interval_seconds=0,
        max_dispatch_attempts=3,
        ui_check=UICheckConfig(
            launch_cmd=["npx", "vite", "--port", str(TEST_PORT), "--host", "127.0.0.1"],
            cwd=str(TEST_APP_DIR),
            url=f"http://127.0.0.1:{TEST_PORT}",
            ui_port=TEST_PORT,
            startup_wait_seconds=15,
        ),
    )


# ── Screenshot module tests ───────────────────────────────────────

class TestScreenshotModule:

    def test_kill_port_before_launch(self):
        """Start a dummy process on port, verify kill_port clears it."""
        # Launch Vite briefly
        _kwargs = {"cwd": str(TEST_APP_DIR), "stdout": subprocess.PIPE, "stderr": subprocess.PIPE}
        if os.name == "nt":
            _kwargs["shell"] = True
            _kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
        proc = subprocess.Popen(
            ["npx", "vite", "--port", str(TEST_PORT), "--host", "127.0.0.1"],
            **_kwargs,
        )
        # Wait for it to bind
        for _ in range(20):
            if not is_port_free(TEST_PORT):
                break
            time.sleep(0.5)
        assert not is_port_free(TEST_PORT), "Vite didn't start"

        # Now kill it via kill_port
        kill_port(TEST_PORT)
        time.sleep(1)

        # Port should be free (or process dying)
        # Give it a moment
        for _ in range(10):
            if is_port_free(TEST_PORT):
                break
            time.sleep(0.5)
        assert is_port_free(TEST_PORT), "Port still in use after kill_port"

    def test_launch_and_kill_app(self):
        """Launch app, verify it's running, kill it, verify port free."""
        app = launch_app(
            cmd=["npx", "vite", "--port", str(TEST_PORT), "--host", "127.0.0.1"],
            cwd=str(TEST_APP_DIR),
            port=TEST_PORT,
            startup_wait=15,
        )
        assert app is not None, "App failed to launch"
        assert not is_port_free(TEST_PORT), "Port free even though app should be running"

        kill_app(app)
        time.sleep(1)

        for _ in range(10):
            if is_port_free(TEST_PORT):
                break
            time.sleep(0.5)
        assert is_port_free(TEST_PORT), "Port still in use after kill_app"

    def test_screenshot_captures_real_image(self, tmp_path):
        """Launch app, take screenshot, verify it's a real PNG."""
        app = launch_app(
            cmd=["npx", "vite", "--port", str(TEST_PORT), "--host", "127.0.0.1"],
            cwd=str(TEST_APP_DIR),
            port=TEST_PORT,
            startup_wait=15,
        )
        assert app is not None

        try:
            out_dir = str(tmp_path / "screenshots")
            path = take_screenshot(
                url=f"http://127.0.0.1:{TEST_PORT}",
                output_dir=out_dir,
                filename="test.png",
            )
            assert path is not None, "Screenshot returned None"
            p = Path(path)
            assert p.exists(), "Screenshot file doesn't exist"
            assert p.stat().st_size > 1000, f"Screenshot too small ({p.stat().st_size} bytes)"
            # Verify PNG header
            with open(p, "rb") as f:
                header = f.read(4)
            assert header == b'\x89PNG', "Not a valid PNG file"
        finally:
            kill_app(app)


# ── Functional probe tests ────────────────────────────────────────

class TestFunctionalProbe:

    def test_probe_passes_on_running_app(self, config):
        """Functional probe launches app, checks health, captures screenshot."""
        req = {"required_output_files_json": "[]"}
        result = functional_probe("T-1", req, config)
        assert result.passed, f"Probe failed: {result.note}"
        assert result.tier == "functional"
        # Screenshot should be captured
        if result.screenshot_path:
            assert Path(result.screenshot_path).exists()

    def test_probe_fails_on_bad_port(self, tmp_path):
        """Probe fails gracefully when app can't launch."""
        bad_config = ProjectConfig(
            engine_root=tmp_path,
            project_root=tmp_path,
            workspace_root=tmp_path,
            deliverable_root=tmp_path,
            db_path=tmp_path / "db",
            artifacts_dir=tmp_path / "art",
            checks_dir=tmp_path / "chk",
            qa_reports_dir=tmp_path / "rpt",
            forge_agent="f",
            models={"forge": "m", "vision": "m"},
            forge_timeout_seconds=10,
            cycle_interval_seconds=0,
            max_dispatch_attempts=1,
            ui_check=UICheckConfig(
                launch_cmd=["nonexistent-command-xyz"],
                cwd=str(tmp_path),
                url="http://127.0.0.1:49999",
                ui_port=49999,
                startup_wait_seconds=3,
            ),
        )
        result = functional_probe("T-BAD", {}, bad_config)
        assert not result.passed

    def test_no_orphan_processes_after_probe(self, config):
        """After probe completes, no Vite/node processes left on the port."""
        req = {"required_output_files_json": "[]"}
        functional_probe("T-1", req, config)
        time.sleep(1)
        # Port should be free
        for _ in range(10):
            if is_port_free(TEST_PORT):
                break
            time.sleep(0.5)
        assert is_port_free(TEST_PORT), "Orphan process still on port after probe"


# ── E2E test (Tier 3) ────────────────────────────────────────────

class TestE2ETest:

    def test_e2e_passes_with_passing_script(self, tmp_path, config):
        """A QA script that exits 0 passes the E2E check."""
        script = tmp_path / "checks" / "qa" / "test_pass.py"
        script.parent.mkdir(parents=True)
        script.write_text("import sys; sys.exit(0)", encoding="utf-8")

        req = {"qa_cmd_json": json.dumps([["python", str(script)]])}
        result = e2e_test("T-1", req, config, blocking=True)
        assert result.passed

    def test_e2e_fails_with_failing_script(self, tmp_path, config):
        """A QA script that exits 1 fails the E2E check (blocking mode)."""
        script = tmp_path / "checks" / "qa" / "test_fail.py"
        script.parent.mkdir(parents=True)
        script.write_text("import sys; print('assertion failed'); sys.exit(1)", encoding="utf-8")

        req = {"qa_cmd_json": json.dumps([["python", str(script)]])}
        result = e2e_test("T-1", req, config, blocking=True)
        assert not result.passed
        assert "assertion failed" in result.note

    def test_e2e_warning_mode_doesnt_block(self, tmp_path, config):
        """In warning mode, a failing script still returns passed=True."""
        script = tmp_path / "checks" / "qa" / "test_warn.py"
        script.parent.mkdir(parents=True)
        script.write_text("import sys; print('not quite right'); sys.exit(1)", encoding="utf-8")

        req = {"qa_cmd_json": json.dumps([["python", str(script)]])}
        result = e2e_test("T-1", req, config, blocking=False)
        assert result.passed  # warning mode doesn't block
        assert result.metadata.get("e2e_warning") is True

    def test_e2e_skips_with_no_cmd(self, config):
        """No qa_cmd_json means E2E is skipped (passes)."""
        result = e2e_test("T-1", {"qa_cmd_json": "[]"}, config)
        assert result.passed


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
