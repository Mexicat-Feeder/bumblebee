"""
Preflight gate — enforces that process documentation was read before
seed scripts or the executor can run.

PREFLIGHT.md is a per-project file with fill-in-the-blank questions
and toggle flags. The blanks require knowledge from the docs (you can't
fake them without reading). The toggles are the final acknowledgement.

Both the seed script and executor call `check()` at startup.
If any answer is blank or any toggle is 0, the process halts with
a clear message about what's missing.
"""

from pathlib import Path
from dataclasses import dataclass
import re
import logging

log = logging.getLogger(__name__)


@dataclass
class PreflightItem:
    key: str
    prompt: str
    expected: str | None  # None = any non-blank answer; string = must match exactly
    value: str
    toggle_key: str
    toggle_value: bool


@dataclass
class PreflightResult:
    passed: bool
    items: list[PreflightItem]
    errors: list[str]


# ── Template generation ──────────────────────────────────────────

TEMPLATE = """# PREFLIGHT — {project_name}
#
# This file gates the seed script and executor. Neither will run
# unless ALL blanks are filled in AND all toggles are set to 1.
#
# PURPOSE: Prove that you actually read the documentation before
# writing specs and seeding tickets. The fill-in-the-blank answers
# require specific knowledge from the docs — you cannot guess them.
#
# DO NOT mark toggles as 1 unless you have genuinely completed the step.
# DO NOT fill in answers by guessing — read the referenced docs.
#
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# ── 1. Engine schema (read: bumblebee/engine/event_log.py) ──────
#
# What module path contains TICKETS_SCHEMA, TICKET_REQUIREMENTS_SCHEMA,
# and TICKET_EVENTS_SCHEMA?
schema_module: ___

# What column in ticket_requirements holds the full spec text?
spec_column: ___

# What is the EventLog method name for recording state transitions?
event_method: ___

schema_verified: 0

# ── 2. Spec rules (read: bumblebee/SPEC-RULES.md) ──────────────
#
# Max context files per ticket? (Rule 4)
max_context_files: ___

# Can required_output_files contain files that already exist on disk? (Rule 5)
existing_files_allowed: ___

# Who writes shared integration files like +page.svelte? (Rule 6)
shared_file_owner: ___

# What must every Svelte spec say about design-tokens.css? (Rule 9)
css_import_rule: ___

spec_rules_verified: 0

# ── 3. Output file checks (manual verification) ────────────────
#
# How many unique output files across all tickets?
total_output_files: ___

# Do any output files appear in multiple tickets? (yes/no)
duplicate_files: ___

# Do any output files already exist on disk? (yes/no)
existing_on_disk: ___

output_files_verified: 0

# ── 4. Decomposition process (read at Phase 0 only) ────────────
#    (read: bumblebee/DECOMPOSITION-PROCESS.md)
#
# What are the four phases in order?
phase_names: ___

# What does qa_verified actually prove? (hint: not integration)
qa_verified_means: ___

decomp_process_verified: 0

# ── 5. Q&A checklist (read: DECOMPOSITION-PROCESS.md → Q&A Checklist) ─
#
# Was the Q&A checklist reviewed before writing specs?
# Name one question you asked the human that the PRD didn't answer:
qa_question_asked: ___

# What LLM model (if any) does this project target? (exact model ID or "none")
qa_target_model: ___

qa_checklist_verified: 0
"""


def generate(project_root: str | Path, project_name: str) -> Path:
    """Generate a blank PREFLIGHT.md in the project directory."""
    p = Path(project_root) / "PREFLIGHT.md"
    content = TEMPLATE.format(project_name=project_name)
    p.write_text(content, encoding="utf-8")
    log.info("Generated PREFLIGHT.md at %s", p)
    return p


# ── Parsing ──────────────────────────────────────────────────────

_KV_RE = re.compile(r"^(\w+):\s*(.*)$")


def _parse(path: Path) -> dict[str, str]:
    """Parse key: value pairs from PREFLIGHT.md, ignoring comments."""
    result = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = _KV_RE.match(line)
        if m:
            result[m.group(1)] = m.group(2).strip()
    return result


# ── Validation ───────────────────────────────────────────────────

# Expected answers (exact match, case-insensitive)
EXPECTED_ANSWERS = {
    "schema_module": "bumblebee/engine/event_log.py",
    "spec_column": "ticket_description",
    "event_method": "record",
    "max_context_files": "3",
    "existing_files_allowed": "no",
    "shared_file_owner": "pixel",
    "duplicate_files": "no",
    "existing_on_disk": "no",
}

# These just need to be non-blank (free-form answers)
FREEFORM_KEYS = {
    "css_import_rule",
    "total_output_files",
    "phase_names",
    "qa_verified_means",
    "qa_question_asked",
    "qa_target_model",
}

# Toggle keys that must be "1"
TOGGLE_KEYS = {
    "schema_verified",
    "spec_rules_verified",
    "output_files_verified",
    "decomp_process_verified",
    "qa_checklist_verified",
}


def check(project_root: str | Path) -> PreflightResult:
    """
    Validate PREFLIGHT.md. Returns PreflightResult with pass/fail and errors.
    Call this from seed scripts and the executor.
    """
    path = Path(project_root) / "PREFLIGHT.md"
    errors: list[str] = []

    if not path.exists():
        return PreflightResult(
            passed=False, items=[],
            errors=["PREFLIGHT.md not found. Run preflight.generate() first."]
        )

    kv = _parse(path)

    # Check expected-answer fields
    for key, expected in EXPECTED_ANSWERS.items():
        val = kv.get(key, "___")
        if val == "___" or not val:
            errors.append(f"  {key}: blank (fill in the answer)")
        elif val.lower() != expected.lower():
            errors.append(f"  {key}: '{val}' (expected '{expected}')")

    # Check freeform fields (just need non-blank)
    for key in FREEFORM_KEYS:
        val = kv.get(key, "___")
        if val == "___" or not val:
            errors.append(f"  {key}: blank (fill in the answer)")

    # Check toggles
    for key in TOGGLE_KEYS:
        val = kv.get(key, "0")
        if val != "1":
            errors.append(f"  {key}: not toggled (set to 1 after completing the section)")

    passed = len(errors) == 0
    return PreflightResult(passed=passed, items=[], errors=errors)


def require(project_root: str | Path, context: str = "script") -> None:
    """
    Check preflight and raise SystemExit if it fails.
    Use at the top of seed scripts and executors.
    """
    result = check(project_root)
    if not result.passed:
        print(f"\n{'='*60}")
        print(f"PREFLIGHT FAILED — {context} cannot proceed")
        print(f"{'='*60}")
        print(f"Fix these items in PREFLIGHT.md:\n")
        for e in result.errors:
            print(e)
        print(f"\nPath: {Path(project_root) / 'PREFLIGHT.md'}")
        print(f"{'='*60}\n")
        raise SystemExit(1)
