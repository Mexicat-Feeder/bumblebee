"""
Swarm Engine — Post-Write Cleanup & Build Check

Runs after Forge writes files:
  1. Strip BOMs from all written files
  2. Run a build check (npm/vite build) to catch import errors early
"""
from __future__ import annotations

import logging
import os
import subprocess
from pathlib import Path

from .config import ProjectConfig

log = logging.getLogger(__name__)


def strip_bom(file_path: str | Path) -> bool:
    """Strip UTF-8 BOM from a file if present. Returns True if BOM was stripped."""
    p = Path(file_path)
    if not p.exists():
        return False
    try:
        raw = p.read_bytes()
        if raw[:3] == b'\xef\xbb\xbf':
            p.write_bytes(raw[3:])
            log.info(f"Stripped BOM from {p.name}")
            return True
    except Exception as e:
        log.warning(f"Failed to check BOM for {p}: {e}")
    return False


def strip_boms_from_files(file_paths: list[str], deliverable_root: Path) -> int:
    """Strip BOMs from a list of relative file paths. Returns count stripped."""
    count = 0
    for rel in file_paths:
        p = deliverable_root / rel
        if strip_bom(p):
            count += 1
    return count


def run_build_check(config: ProjectConfig) -> tuple[bool, str]:
    """
    Run a build check (vite build) to catch compile errors.
    Returns (passed, error_output).
    
    Only runs when the project is buildable — needs package.json,
    a bundler config (vite.config.*), and an entry point (index.html or src/main.*).
    Skips gracefully if the scaffold isn't complete yet.
    """
    root = config.deliverable_root
    cwd = str(root)

    # Only run if the project has all the pieces needed to build
    if not (root / "package.json").exists():
        return True, "no package.json, skipping build check"

    # Need a bundler config
    has_vite_config = any((
        (root / "vite.config.ts").exists(),
        (root / "vite.config.js").exists(),
        (root / "vite.config.mjs").exists(),
    ))
    if not has_vite_config:
        return True, "no vite config yet, skipping build check"

    # Need an entry point
    has_entry = (root / "index.html").exists()
    if not has_entry:
        return True, "no index.html yet, skipping build check"

    # Only run the build check if ALL expected source files exist.
    # During multi-gate builds, early gates will have missing imports
    # that are created by later gates. Build check at that point would
    # always fail and block legitimate progress.
    # The build check becomes meaningful after the final gate.
    #
    # Heuristic: if main.tsx references App and App doesn't exist, skip.
    # More generally: skip if there are known unresolved imports.
    main_tsx = root / "src" / "main.tsx"
    app_tsx = root / "src" / "App.tsx"
    if main_tsx.exists() and not app_tsx.exists():
        return True, "App.tsx not yet created, skipping build check"

    # Ensure node_modules
    from .screenshot import ensure_node_modules
    if not ensure_node_modules(cwd):
        return False, "npm install failed"

    # Try vite build
    try:
        result = subprocess.run(
            ["npx", "vite", "build"],
            cwd=cwd,
            capture_output=True, text=True, timeout=60,
            shell=(os.name == "nt"),
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        if result.returncode == 0:
            return True, "build passed"
        else:
            error = (result.stdout + result.stderr)[-1000:]
            return False, f"build failed: {error}"
    except subprocess.TimeoutExpired:
        return False, "build timed out after 60s"
    except Exception as e:
        return False, f"build check error: {e}"


def compute_relative_import(from_file: str, to_file: str) -> str:
    """
    Compute the correct relative import path from one file to another.
    
    Example:
        from_file = "src/components/base/Card.tsx"
        to_file = "src/styles/design-tokens.css"
        returns "../../styles/design-tokens.css"
    """
    from_parts = Path(from_file).parent.parts
    to_parts = Path(to_file).parts

    # Find common prefix length
    common = 0
    for a, b in zip(from_parts, to_parts):
        if a == b:
            common += 1
        else:
            break

    # Go up from from_file's directory
    ups = len(from_parts) - common
    # Go down to to_file
    remaining = to_parts[common:]

    if ups == 0:
        return "./" + "/".join(remaining)
    return "/".join([".."] * ups + list(remaining))
