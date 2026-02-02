"""Tests for template syntax validation."""

from __future__ import annotations

from jinja2 import TemplateSyntaxError

from prisme.utils.template_engine import create_template_environment


def test_all_templates_have_valid_syntax():
    """Test that all templates in the template directory have valid Jinja2 syntax.

    This test will:
    1. Load all templates from the templates/jinja2 directory
    2. Attempt to compile each template
    3. Fail if any template has syntax errors

    Note: This test will pass with 0 templates initially, and will validate
    templates as they are added during the migration.
    """
    env = create_template_environment()

    if env.loader is None:
        # No templates to validate
        return

    template_names = env.list_templates()

    syntax_errors = []
    for template_name in template_names:
        try:
            # This will raise TemplateSyntaxError if template has syntax errors
            env.get_template(template_name)
        except TemplateSyntaxError as e:
            syntax_errors.append(f"{template_name}: {e}")

    if syntax_errors:
        error_msg = "Template syntax errors found:\n" + "\n".join(syntax_errors)
        raise AssertionError(error_msg)


def test_template_extensions():
    """Test that only .jinja2 files are in the template directory."""
    env = create_template_environment()

    if env.loader is None:
        return

    template_names = env.list_templates()

    # Filter out .gitkeep files
    template_files = [t for t in template_names if not t.endswith(".gitkeep")]

    invalid_extensions = [t for t in template_files if not t.endswith(".jinja2")]

    if invalid_extensions:
        error_msg = "Non-.jinja2 files found in template directory:\n" + "\n".join(
            invalid_extensions
        )
        raise AssertionError(error_msg)
