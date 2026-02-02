"""Tests for protected region parsing, merging, and write_file_with_strategy integration."""

from __future__ import annotations

from pathlib import Path

from prisme.spec.stack import FileStrategy
from prisme.utils.file_handler import (
    merge_protected_regions,
    parse_protected_regions,
    write_file_with_strategy,
)


class TestParseProtectedRegions:
    """Tests for parse_protected_regions()."""

    def test_parse_python_style_comments(self) -> None:
        content = (
            "# some code\n"
            "# PRISM:PROTECTED:START - Custom Logic\n"
            "my_var = 42\n"
            "# PRISM:PROTECTED:END\n"
            "# more code\n"
        )
        parsed = parse_protected_regions(content)
        assert "Custom Logic" in parsed.protected_regions
        assert parsed.protected_regions["Custom Logic"].content == "my_var = 42"

    def test_parse_js_style_comments(self) -> None:
        content = (
            "const x = 1;\n"
            "// PRISM:PROTECTED:START - Custom Imports\n"
            "import Foo from './Foo';\n"
            "// PRISM:PROTECTED:END\n"
        )
        parsed = parse_protected_regions(content)
        assert "Custom Imports" in parsed.protected_regions
        assert parsed.protected_regions["Custom Imports"].content == "import Foo from './Foo';"

    def test_parse_jsx_style_comments(self) -> None:
        content = (
            "  {/* PRISM:PROTECTED:START - Custom Providers */}\n"
            "  <MyProvider>\n"
            "  {/* PRISM:PROTECTED:END */}\n"
        )
        parsed = parse_protected_regions(content)
        assert "Custom Providers" in parsed.protected_regions
        assert parsed.protected_regions["Custom Providers"].content == "  <MyProvider>"

    def test_parse_multiple_regions(self) -> None:
        content = (
            "// PRISM:PROTECTED:START - Region A\n"
            "a\n"
            "// PRISM:PROTECTED:END\n"
            "// PRISM:PROTECTED:START - Region B\n"
            "b\n"
            "// PRISM:PROTECTED:END\n"
        )
        parsed = parse_protected_regions(content)
        assert len(parsed.protected_regions) == 2
        assert parsed.protected_regions["Region A"].content == "a"
        assert parsed.protected_regions["Region B"].content == "b"

    def test_parse_empty_region(self) -> None:
        content = "// PRISM:PROTECTED:START - Empty\n// PRISM:PROTECTED:END\n"
        parsed = parse_protected_regions(content)
        assert "Empty" in parsed.protected_regions
        assert parsed.protected_regions["Empty"].content == ""

    def test_parse_no_regions(self) -> None:
        content = "just some code\nno markers here\n"
        parsed = parse_protected_regions(content)
        assert len(parsed.protected_regions) == 0


class TestMergeProtectedRegions:
    """Tests for merge_protected_regions()."""

    def test_merge_restores_old_content(self) -> None:
        old_regions = parse_protected_regions(
            "// PRISM:PROTECTED:START - Custom Imports\n"
            "import Real from './Real';\n"
            "// PRISM:PROTECTED:END\n"
        ).protected_regions

        new_content = (
            "// PRISM:PROTECTED:START - Custom Imports\n// placeholder\n// PRISM:PROTECTED:END\n"
        )

        merged = merge_protected_regions(new_content, old_regions)
        assert "import Real from './Real';" in merged
        assert "placeholder" not in merged

    def test_merge_jsx_style(self) -> None:
        old_regions = parse_protected_regions(
            "  {/* PRISM:PROTECTED:START - Custom Providers */}\n"
            "  <AuthProvider>\n"
            "  {/* PRISM:PROTECTED:END */}\n"
        ).protected_regions

        new_content = (
            "  {/* PRISM:PROTECTED:START - Custom Providers */}\n"
            "  {/* placeholder */}\n"
            "  {/* PRISM:PROTECTED:END */}\n"
        )

        merged = merge_protected_regions(new_content, old_regions)
        assert "<AuthProvider>" in merged
        assert "placeholder" not in merged

    def test_merge_preserves_unmatched_regions(self) -> None:
        """If new content has a region not in old, it stays as-is."""
        merged = merge_protected_regions(
            "// PRISM:PROTECTED:START - New Region\n// default\n// PRISM:PROTECTED:END\n",
            {},
        )
        assert "// default" in merged

    def test_merge_multiple_regions(self) -> None:
        old = parse_protected_regions(
            "// PRISM:PROTECTED:START - A\nold_a\n// PRISM:PROTECTED:END\n"
            "// PRISM:PROTECTED:START - B\nold_b\n// PRISM:PROTECTED:END\n"
        ).protected_regions

        new = (
            "// PRISM:PROTECTED:START - A\nnew_a\n// PRISM:PROTECTED:END\n"
            "// PRISM:PROTECTED:START - B\nnew_b\n// PRISM:PROTECTED:END\n"
        )

        merged = merge_protected_regions(new, old)
        assert "old_a" in merged
        assert "old_b" in merged
        assert "new_a" not in merged
        assert "new_b" not in merged


class TestWriteFileWithStrategyProtectedRegions:
    """Tests for write_file_with_strategy() preserving protected regions."""

    def test_preserves_protected_content_on_overwrite(self, tmp_path: Path) -> None:
        target = tmp_path / "router.tsx"

        # Write initial file with user's custom content
        target.write_text(
            "// PRISM:PROTECTED:START - Custom Imports\n"
            "import Dashboard from './pages/Dashboard';\n"
            "// PRISM:PROTECTED:END\n"
            "const x = 1;\n"
        )

        # New generated content with placeholder
        new_content = (
            "// PRISM:PROTECTED:START - Custom Imports\n"
            "// Add your custom imports here\n"
            "// PRISM:PROTECTED:END\n"
            "const x = 2;\n"
        )

        written = write_file_with_strategy(target, new_content, FileStrategy.ALWAYS_OVERWRITE)
        assert written is True

        result = target.read_text()
        assert "import Dashboard from './pages/Dashboard';" in result
        assert "Add your custom imports" not in result
        assert "const x = 2;" in result

    def test_preserves_jsx_protected_content(self, tmp_path: Path) -> None:
        target = tmp_path / "App.tsx"

        target.write_text(
            "  {/* PRISM:PROTECTED:START - Custom Providers */}\n"
            "  <ThemeProvider>\n"
            "  {/* PRISM:PROTECTED:END */}\n"
        )

        new_content = (
            "  {/* PRISM:PROTECTED:START - Custom Providers */}\n"
            "  {/* Wrap with providers */}\n"
            "  {/* PRISM:PROTECTED:END */}\n"
        )

        write_file_with_strategy(target, new_content, FileStrategy.ALWAYS_OVERWRITE)

        result = target.read_text()
        assert "<ThemeProvider>" in result
        assert "Wrap with providers" not in result

    def test_no_protected_regions_writes_normally(self, tmp_path: Path) -> None:
        target = tmp_path / "plain.py"
        target.write_text("old content\n")

        write_file_with_strategy(target, "new content\n", FileStrategy.ALWAYS_OVERWRITE)
        assert target.read_text() == "new content\n"

    def test_new_file_writes_normally(self, tmp_path: Path) -> None:
        target = tmp_path / "new.py"

        write_file_with_strategy(
            target,
            "// PRISM:PROTECTED:START - Region\n// default\n// PRISM:PROTECTED:END\n",
            FileStrategy.ALWAYS_OVERWRITE,
        )
        assert "// default" in target.read_text()
