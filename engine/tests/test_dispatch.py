"""Tests for Forge dispatch (structured contract)."""
import json
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from engine.dispatch import (
    DispatchContract, DispatchResult,
    build_contract, format_task_message,
)


class TestContractBuilding:

    def test_contract_includes_all_required_fields(self):
        requirements = {
            "ticket_description": "Create Button component",
            "required_output_files_json": '["src/components/Button.tsx"]',
            "worker_done_criteria": "File exists and exports default",
            "context_files_json": '["src/App.tsx"]',
            "constraints_json": '["TypeScript only"]',
            "interaction_spec": "Button renders with label text",
        }
        contract = build_contract("T-1", requirements, _mock_config(), attempt=1)
        assert contract.task_id == "T-1"
        assert contract.objective == "Create Button component"
        assert contract.files_to_write == ["src/components/Button.tsx"]
        assert contract.files_to_read == ["src/App.tsx"]
        assert contract.constraints == ["TypeScript only"]
        assert contract.interaction_spec == "Button renders with label text"
        assert contract.success_criteria == "File exists and exports default"

    def test_contract_omits_error_context_after_3_attempts(self):
        requirements = {"ticket_description": "Fix bug"}
        contract = build_contract(
            "T-1", requirements, _mock_config(),
            attempt=3, last_error="previous tsc error"
        )
        assert contract.error_context is None

    def test_contract_includes_error_context_before_3_attempts(self):
        requirements = {"ticket_description": "Fix bug"}
        contract = build_contract(
            "T-1", requirements, _mock_config(),
            attempt=2, last_error="previous tsc error"
        )
        assert contract.error_context == "previous tsc error"

    def test_contract_includes_screenshot_when_available(self):
        requirements = {"ticket_description": "UI work"}
        contract = build_contract(
            "T-1", requirements, _mock_config(),
            app_screenshot_b64="iVBOR..."
        )
        assert contract.app_screenshot_b64 == "iVBOR..."

    def test_contract_architecture_rules_passed_through(self):
        requirements = {"ticket_description": "Create component"}
        rules = ["No Node.js built-ins in src/", "Use design-tokens.css"]
        contract = build_contract(
            "T-1", requirements, _mock_config(),
            architecture_rules=rules
        )
        assert contract.architecture_rules == rules


class TestTaskFormatting:

    def test_format_includes_objective(self):
        contract = DispatchContract(
            task_id="T-1",
            objective="Create Button.tsx",
            files_to_write=["src/Button.tsx"],
        )
        msg = format_task_message(contract)
        assert "Create Button.tsx" in msg
        assert "src/Button.tsx" in msg

    def test_format_includes_architecture_rules(self):
        contract = DispatchContract(
            task_id="T-1",
            objective="test",
            files_to_write=[],
            architecture_rules=["No fs in src/", "Default exports only"],
        )
        msg = format_task_message(contract)
        assert "No fs in src/" in msg
        assert "Default exports only" in msg

    def test_format_includes_interaction_spec(self):
        contract = DispatchContract(
            task_id="T-1",
            objective="test",
            files_to_write=[],
            interaction_spec="Click button → modal opens",
        )
        msg = format_task_message(contract)
        assert "Click button" in msg

    def test_format_includes_error_context(self):
        contract = DispatchContract(
            task_id="T-1",
            objective="test",
            files_to_write=[],
            error_context="TypeError: cannot read property 'map'",
        )
        msg = format_task_message(contract)
        assert "TypeError" in msg
        assert "Previous attempt error" in msg

    def test_format_omits_empty_optional_fields(self):
        contract = DispatchContract(
            task_id="T-1",
            objective="simple task",
            files_to_write=["f.ts"],
        )
        msg = format_task_message(contract)
        assert "Previous attempt error" not in msg
        assert "Interaction spec" not in msg
        assert "Files to read" not in msg

    def test_format_notes_screenshot_attached(self):
        contract = DispatchContract(
            task_id="T-1",
            objective="test",
            files_to_write=[],
            app_screenshot_b64="data...",
        )
        msg = format_task_message(contract)
        assert "screenshot" in msg.lower()

    def test_contract_to_json(self):
        contract = DispatchContract(
            task_id="T-1",
            objective="Create component",
            files_to_write=["src/X.tsx"],
            architecture_rules=["rule1"],
            attempt=2,
        )
        j = json.loads(contract.to_json())
        assert j["task_id"] == "T-1"
        assert j["attempt"] == 2
        assert "rule1" in j["architecture_rules"]


class TestNoHardcodedModels:

    def test_dispatch_module_no_model_strings(self):
        """dispatch.py must not contain hardcoded model names."""
        dispatch_path = Path(__file__).resolve().parents[1] / "dispatch.py"
        content = dispatch_path.read_text(encoding="utf-8")
        model_patterns = ["qwen", "lemonade/", "kokoro", "gpt-", "claude-"]
        for pattern in model_patterns:
            assert pattern not in content.lower(), (
                f"Hardcoded model name '{pattern}' found in dispatch.py"
            )


# ── Helpers ───────────────────────────────────────────────────────

def _mock_config():
    """Minimal config for contract building tests."""
    from engine.config import ProjectConfig
    return ProjectConfig(
        engine_root=Path("."),
        project_root=Path("."),
        workspace_root=Path("."),
        deliverable_root=Path("."),
        db_path=Path("test.db"),
        artifacts_dir=Path("artifacts"),
        checks_dir=Path("checks"),
        qa_reports_dir=Path("reports"),
        forge_agent="forge",
        models={"forge": "test/model", "vision": "test/model"},
        forge_timeout_seconds=60,
        cycle_interval_seconds=10,
        max_dispatch_attempts=3,
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
