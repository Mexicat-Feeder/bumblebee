"""Tests for post-write cleanup."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from engine.postwrite import strip_bom, strip_boms_from_files, compute_relative_import


class TestBOMStripping:

    def test_strips_bom(self, tmp_path):
        f = tmp_path / "test.tsx"
        f.write_bytes(b'\xef\xbb\xbfimport React from "react";')
        assert strip_bom(f)
        assert f.read_bytes()[:6] == b'import'

    def test_no_bom_no_change(self, tmp_path):
        f = tmp_path / "clean.tsx"
        f.write_text("import React from 'react';", encoding="utf-8")
        assert not strip_bom(f)

    def test_strip_from_file_list(self, tmp_path):
        (tmp_path / "src").mkdir()
        f1 = tmp_path / "src" / "a.tsx"
        f2 = tmp_path / "src" / "b.tsx"
        f1.write_bytes(b'\xef\xbb\xbfconst a = 1;')
        f2.write_text("const b = 2;", encoding="utf-8")
        count = strip_boms_from_files(["src/a.tsx", "src/b.tsx"], tmp_path)
        assert count == 1

    def test_missing_file_safe(self, tmp_path):
        assert not strip_bom(tmp_path / "nonexistent.tsx")


class TestImportPathComputation:

    def test_same_directory(self):
        assert compute_relative_import(
            "src/components/A.tsx", "src/components/B.tsx"
        ) == "./B.tsx"

    def test_one_level_up(self):
        assert compute_relative_import(
            "src/components/base/Card.tsx", "src/components/utils.ts"
        ) == "../utils.ts"

    def test_two_levels_up(self):
        result = compute_relative_import(
            "src/components/base/Card.tsx", "src/styles/design-tokens.css"
        )
        assert result == "../../styles/design-tokens.css"

    def test_deep_to_shallow(self):
        result = compute_relative_import(
            "src/components/panels/library/FileTree.tsx", "src/shared/api-types.ts"
        )
        assert result == "../../../shared/api-types.ts"

    def test_shallow_to_deep(self):
        result = compute_relative_import(
            "src/App.tsx", "src/components/base/Card.tsx"
        )
        assert result == "./components/base/Card.tsx"


class TestNoHardcodedStrings:

    def test_postwrite_no_model_names(self):
        path = Path(__file__).resolve().parents[1] / "postwrite.py"
        content = path.read_text(encoding="utf-8")
        for p in ["qwen", "lemonade/", "kokoro"]:
            assert p not in content.lower()

    def test_postwrite_no_hardcoded_paths(self):
        path = Path(__file__).resolve().parents[1] / "postwrite.py"
        content = path.read_text(encoding="utf-8")
        for p in ["bumblebee", "agent-swarm"]:
            assert p not in content.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
