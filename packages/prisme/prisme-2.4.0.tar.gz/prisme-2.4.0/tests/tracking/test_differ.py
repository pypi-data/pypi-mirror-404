"""Tests for the diff generator."""

from __future__ import annotations

from prisme.tracking.differ import DiffGenerator, DiffSummary


def test_diff_summary_no_changes():
    """Test diff summary with no changes."""
    content = "line 1\nline 2\nline 3"
    summary = DiffGenerator.diff_summary(content, content)

    assert summary.lines_added == 0
    assert summary.lines_removed == 0
    assert summary.lines_changed == 0


def test_diff_summary_additions():
    """Test diff summary with additions."""
    old = "line 1\nline 2"
    new = "line 1\nline 2\nline 3\nline 4"

    summary = DiffGenerator.diff_summary(old, new)

    assert summary.lines_added == 2
    assert summary.lines_removed == 0


def test_diff_summary_deletions():
    """Test diff summary with deletions."""
    old = "line 1\nline 2\nline 3\nline 4"
    new = "line 1\nline 2"

    summary = DiffGenerator.diff_summary(old, new)

    assert summary.lines_added == 0
    assert summary.lines_removed == 2


def test_diff_summary_modifications():
    """Test diff summary with modifications."""
    old = "line 1\nline 2\nline 3"
    new = "line 1\nmodified line 2\nline 3"

    summary = DiffGenerator.diff_summary(old, new)

    assert summary.lines_changed == 1


def test_diff_summary_complex_changes():
    """Test diff summary with mixed changes."""
    old = "line 1\nline 2\nline 3\nline 4"
    new = "line 1\nmodified line 2\nline 3\nline 5\nline 6"

    summary = DiffGenerator.diff_summary(old, new)

    # One line changed (line 2), and overall adds/removes balanced
    assert summary.lines_changed > 0


def test_diff_summary_to_dict():
    """Test converting diff summary to dictionary."""
    summary = DiffSummary(lines_added=5, lines_removed=2, lines_changed=3)
    data = summary.to_dict()

    assert data["lines_added"] == 5
    assert data["lines_removed"] == 2
    assert data["lines_changed"] == 3


def test_generate_diff_no_changes():
    """Test generating diff with no changes."""
    content = "line 1\nline 2\nline 3"
    diff = DiffGenerator.generate_diff(content, content)

    # No changes = empty diff (or just headers)
    assert diff == "" or "@@" not in diff


def test_generate_diff_additions():
    """Test generating diff with additions."""
    old = "line 1\nline 2"
    new = "line 1\nline 2\nline 3"

    diff = DiffGenerator.generate_diff(old, new)

    assert "+line 3" in diff
    assert "@@" in diff  # Should have chunk header


def test_generate_diff_deletions():
    """Test generating diff with deletions."""
    old = "line 1\nline 2\nline 3"
    new = "line 1\nline 2"

    diff = DiffGenerator.generate_diff(old, new)

    assert "-line 3" in diff
    assert "@@" in diff


def test_generate_diff_modifications():
    """Test generating diff with modifications."""
    old = "line 1\noriginal\nline 3"
    new = "line 1\nmodified\nline 3"

    diff = DiffGenerator.generate_diff(old, new)

    assert "-original" in diff
    assert "+modified" in diff


def test_generate_diff_custom_labels():
    """Test generating diff with custom labels."""
    old = "old content"
    new = "new content"

    diff = DiffGenerator.generate_diff(old, new, old_label="before", new_label="after")

    assert "before" in diff
    assert "after" in diff


def test_format_diff_colored():
    """Test adding ANSI color codes to diff."""
    diff = """--- a/file.py
+++ b/file.py
@@ -1,3 +1,3 @@
 line 1
-old line
+new line
 line 3"""

    colored = DiffGenerator.format_diff_colored(diff)

    # Should contain ANSI escape codes
    assert "\033[" in colored  # ANSI escape sequence present
    assert "old line" in colored
    assert "new line" in colored


def test_format_diff_markdown():
    """Test formatting diff for Markdown."""
    diff = """--- a/file.py
+++ b/file.py
@@ -1,2 +1,2 @@
-old
+new"""

    markdown = DiffGenerator.format_diff_markdown(diff)

    assert markdown.startswith("```diff")
    assert markdown.endswith("```")
    assert diff in markdown


def test_diff_realistic_code_change():
    """Test diff with realistic code change."""
    old_code = """def create_user(data):
    return db.add(User(**data.dict()))
"""

    new_code = """def create_user(data):
    user = User(**data.model_dump())
    # Custom: Send welcome email
    send_welcome_email(user.email)
    return db.add(user)
"""

    summary = DiffGenerator.diff_summary(old_code, new_code)
    diff = DiffGenerator.generate_diff(old_code, new_code)

    # Should detect changes
    assert summary.lines_added > 0 or summary.lines_changed > 0

    # Diff should show both old and new code
    assert "dict()" in diff or "model_dump()" in diff


def test_diff_empty_files():
    """Test diff with empty files."""
    summary = DiffGenerator.diff_summary("", "")
    assert summary.lines_added == 0
    assert summary.lines_removed == 0
    assert summary.lines_changed == 0

    diff = DiffGenerator.generate_diff("", "")
    assert diff == "" or len(diff) < 10  # Minimal or empty


def test_diff_one_empty_file():
    """Test diff when one file is empty."""
    content = "line 1\nline 2\nline 3"

    # Old empty, new has content
    summary1 = DiffGenerator.diff_summary("", content)
    assert summary1.lines_added == 3

    # Old has content, new empty
    summary2 = DiffGenerator.diff_summary(content, "")
    assert summary2.lines_removed == 3
